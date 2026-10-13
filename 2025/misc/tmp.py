import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from ..services.order_services import get_token_for_orders_request, send_orders, receive_set_orders, update_orders, check_update_orders
from datetime import datetime
import json
import logging
import time

_logger = logging.getLogger(__name__)

TRASMISSIONE_BLOCCATA = False

STATO_TRASMISSIONE = [
    ('draft', "Nuova"),
    ('to_send', "Invio in Corso"),
    ('in_progress', "In Elaborazione"),
    ('sending_failed', "Invio Fallito"),
    ('sale', "Elaborata"),
    ('update', "Modificata")
]

token_info = {
    'token': None,
    'expires_in': 0  # timestamp
}

token_lock = threading.Lock()

MAX_RETRIES = 3


def get_valid_token():
    with token_lock:
        if time.time() >= token_info['expires_in']:
            _logger.info("[Token Refresh] Il token è scaduto. Rigenero...")
            token_info['token'] = get_token_for_orders_request()
            token_info['expires_in'] = int(time.time()) + 900  # 15 minuti
        else:
            _logger.info("[Token Valid] Riutilizzo il token esistente.")
        return token_info['token']


class GemsTrasmissioni(models.Model):
    _name = 'trasmissioni'
    _description = 'Trasmissioni'

    nome = fields.Char(string='Codice', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('Nuova'))
    descrizione = fields.Char(string="Etichetta")
    data_creazione = fields.Date(string="Data Creazione", readonly=True)
    id_trasmissione = fields.Char(string="ID Trasmissione", readonly=True)
    linee_trasmissione = fields.One2many(
        comodel_name='linea.trasmissioni',
        inverse_name='gems_trasmissione_id',
        string="Linee trasmissioni",
        copy=True, auto_join=True
    )
    note = fields.Html(
        string="Note Trasmissione",
        store=True, readonly=False
    )
    stato = fields.Selection(
        selection=STATO_TRASMISSIONE,
        string="Stato",
        readonly=True, copy=False, index=True,
        default='draft'
    )

    esito_invio = fields.Char(string="Esito Invio", readonly=True)
    esito_recupero = fields.Char(string="Esito Recupero", readonly=True)

    json_request = fields.Text(string="JSON request")
    json_response = fields.Text(string="JSON response")
    request_time = fields.Datetime(string="Data Trasmissione", readonly=True)
    response_time = fields.Datetime(string="Response Time")

    @api.model
    def create(self, vals):
        if vals.get('nome', _('Nuova')) == _('Nuova'):
            vals['data_creazione'] = fields.Date.today()
            # GENERAZIONE NOME SEQUENCE
            vals['nome'] = self.env['ir.sequence'].next_by_code('gems.trasmissioni.sequence') or _('Nuova')
        return super(GemsTrasmissioni, self).create(vals)

    def calcolo_linee_trasmissioni_json(self, trasmissione_id):
        query = """
                    SELECT json_agg(header)
                    FROM (
                        SELECT json_build_object(
                            'header', json_build_object(
                                'orderNumber', 
                                    CASE 
                                        WHEN ordine IS NOT NULL AND ordine != '' THEN ordine 
                                        ELSE (SELECT descrizione FROM trasmissioni WHERE id = %s) || '.' || row_number() OVER()
                                    END,
                                'orderDate', to_char(CURRENT_DATE, 'YYYY-MM-DD'),
                                'customerCode', codice_cliente,
                                'documentType', 'newTitle'
                            ),
                            'items', json_agg(json_build_object(
                                'eanCode', ean,
                                'quantity', CAST(qty AS INTEGER),
                                'discount', sconto,
                                'paymentTerm', termini
                            ))
                        ) AS header
                        FROM (
                            SELECT 
                                lt.gems_ean AS ean, 
                                sol.product_uom_qty AS qty, 
                                CAST(sol.sconto_occasionale * 100 AS DECIMAL(10,1)) AS sconto, 
                                sol.termini_pagamento_occasionale AS termini, 
                                sol.ordine_cliente AS ordine,
                                rs.gems_codice_azienda AS codice_cliente
                            FROM sale_order_line sol
                            JOIN linea_trasmissioni lt ON sol.gems_linee_trasmissione_id = lt.id
                            JOIN res_partner rs ON sol.order_partner_id = rs.id
                            WHERE lt.gems_trasmissione_id = %s
                        ) AS sub
                        GROUP BY codice_cliente, ordine
                        ORDER BY ordine desc
                    ) t;
                """
        params = [trasmissione_id, trasmissione_id]
        self.env.cr.execute(query, params)
        result = self.env.cr.fetchone()
        return result[0] if result and result[0] else "[]"  # Return JSON string

    def action_invio_trasmissione_json(self):
        if TRASMISSIONE_BLOCCATA:
            raise ValidationError("Non è possibile inviare ordini, prima del Go-live")

        for linea_trasmissione in self.linee_trasmissione:
            linea_trasmissione.gems_totale_prenotazioni_trasmesse = linea_trasmissione.gems_totale_prenotazioni
            for linea_prenotazione in linea_trasmissione.gems_linea_prenotazione_id:
                if not linea_prenotazione.da_trasmettere:
                    linea_prenotazione.gems_linee_trasmissione_id = None
                    linea_trasmissione.write({'gems_linea_prenotazione_id': [(3, linea_prenotazione.id)]})
                else:
                    linea_prenotazione.qty_trasmessa = linea_prenotazione.product_uom_qty
                    linea_prenotazione.qty_trasmessa_old = linea_prenotazione.product_uom_qty
                    linea_prenotazione.qty_trasmessa_original = linea_prenotazione.product_uom_qty
                    linea_prenotazione.sconto_occasionale_trasmesso_original = linea_prenotazione.sconto_occasionale
                    linea_prenotazione.sconto_occasionale_trasmesso = linea_prenotazione.sconto_occasionale
                    linea_prenotazione.termini_pagamento_occasionale_trasmesso_original = linea_prenotazione.termini_pagamento_occasionale
                    linea_prenotazione.termini_pagamento_occasionale_trasmesso = linea_prenotazione.termini_pagamento_occasionale
        self.write({
            'nome': self.nome,
            'stato': 'to_send',
            'request_time': datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.env['export.cedola'].compute_trasmesso(self.linee_trasmissione.ids)

    def invio_trasmissione_segmentata_sequenziale(self, trasmissione, linee_trasmissione_json):
        for linea_trasmissione in linee_trasmissione_json:
            linea_to_send = [linea_trasmissione]
            codice_cliente = linea_trasmissione['header']['customerCode']

            token = get_token_for_orders_request()
            risposta_invio_ordini = send_orders(token, linea_to_send)
            trasmissione.write({
                'stato': 'in_progress'
            })

            for linea_prenotazione in trasmissione.linee_trasmissione.gems_linea_prenotazione_id:
                if linea_prenotazione.order_partner_id.gems_codice_azienda == codice_cliente:
                    linea_prenotazione.write({'request_time': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                                              'json_request': str(linea_to_send),
                                              'id_trasmissione': str(risposta_invio_ordini)})

            self.env.cr.commit()

    def invio_trasmissione_segmentata_concorrente(self, linea_trasmissione, trasmissione_id):
        try:
            token = get_valid_token()
            linea_to_send = [linea_trasmissione]
            codice_cliente = linea_trasmissione['header']['customerCode']
            titoli = []
            for item in linea_trasmissione['items']:
                titoli.append(item['eanCode'])
            risposta_invio_ordini = send_orders(token, linea_to_send)
            return {'trasmissione_id': trasmissione_id,  # lo passo per recuperarlo dopo
                    'codice_cliente': codice_cliente,
                    'titoli': titoli,
                    'request_time': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                    'json_request': str(linea_to_send),
                    'risposta_invio': str(risposta_invio_ordini)}
        except Exception as e:
            e.linea_trasmissione = linea_trasmissione
            e.trasmissione_id = trasmissione_id
            raise e

    def cron_invio_trasmissione(self, clienti_ids=False):
        trasmissioni_to_send = self.env['trasmissioni'].search([('stato', '=', 'to_send')])
        for trasmissione in trasmissioni_to_send:
            _logger.info(f"Invio trasmissione: {trasmissione.id}, {trasmissione.descrizione}")

            # metto ko preventivamente tutte le linee_prenotazione associate alla trasmissione
            linee_prenotazioni = trasmissione.linee_trasmissione.gems_linea_prenotazione_da_mostrare
            linee_prenotazioni.write({'esito_invio': 'ko'})

            linee_trasmissione_json = self.calcolo_linee_trasmissioni_json(trasmissione.id)
            if not linee_trasmissione_json or linee_trasmissione_json == "[]":
                return  # no data
            if clienti_ids:
                results = []
                error_lines = {}  # linee in errore
                with ThreadPoolExecutor(max_workers=16) as executor:
                    futures = {
                        executor.submit(self.invio_trasmissione_segmentata_concorrente, linea_trasmissione, trasmissione.id)
                        for linea_trasmissione in linee_trasmissione_json}

                    for future in as_completed(futures):
                        try:
                            results.append(future.result())
                            _logger.info(f"Risultato ottenuto: {future.result()}")
                        except Exception as e:
                            _logger.warning(f"Errore nel thread: {e}")
                            if hasattr(e, 'linea_trasmissione') and hasattr(e, 'trasmissione_id'):
                                error_lines[(json.dumps(e.linea_trasmissione, sort_keys=True), e.trasmissione_id)] = e
                            else:
                                pass

                for i in range(0, MAX_RETRIES):
                    if error_lines:
                        _logger.warning(f"Tentativo {i + 1}/{MAX_RETRIES} - Retry in corso per {len(error_lines)} linee fallite.")
                        new_error_lines = {}
                        with ThreadPoolExecutor(max_workers=16) as executor:
                            futures = {
                                executor.submit(self.invio_trasmissione_segmentata_concorrente, json.loads(error[0]), error[1])
                                for error in error_lines}

                            for future in as_completed(futures):
                                try:
                                    results.append(future.result())
                                    _logger.info(f"Risultato ottenuto: {future.result()}")
                                except Exception as e:
                                    _logger.warning(f"Errore nel thread: {e}")
                                    if hasattr(e, 'linea_trasmissione') and hasattr(e, 'trasmissione_id'):
                                        new_error_lines[(json.dumps(e.linea_trasmissione, sort_keys=True), e.trasmissione_id)] = e
                                    else:
                                        pass
                        error_lines = new_error_lines

                    if error_lines and i < MAX_RETRIES - 1:
                        time.sleep(5)   # 5 secondi di attesa

                trasmissione_corrente = None

                esito = None

                if error_lines:
                    _logger.error(f"{len(error_lines)} linee hanno fallito dopo {MAX_RETRIES} tentativi:")
                    esito = "Errore durante l'invio della trasmissione, riprova o contatta l'assistenza"
                    for error in error_lines:
                        _logger.error(f"errore: {error_lines[error]}, sulla linea: {error[0]}")
                        trasmissione_corrente = self.env['trasmissioni'].browse(error[1])
                else:
                    _logger.info("Tutte le linee trasmesse correttamente.")

                if results:
                    for res in results:
                        trasmissione_corrente = self.env['trasmissioni'].browse(res['trasmissione_id'])
                        linea_prenotazione = self.env['sale.order.line'].search(
                            [('order_partner_id.gems_codice_azienda', '=', res['codice_cliente']),
                             ('gems_linee_trasmissione_id', 'in', trasmissione_corrente.linee_trasmissione.mapped('id')),
                             ('product_template_id.gems_ean', 'in', res['titoli'])])
                        linea_prenotazione.write({'request_time': res['request_time'],
                                                  'json_request': res['json_request'],
                                                  'id_trasmissione': res['risposta_invio'],
                                                  'esito_invio': 'ok'})
                        if trasmissione_corrente.stato != 'in_progress':
                            trasmissione_corrente.write({
                                'stato': 'in_progress'
                            })
                else:
                    if trasmissione_corrente.stato != 'sending_failed':
                        trasmissione_corrente.write({
                            'stato': 'sending_failed'
                        })

                if esito:
                    trasmissione_corrente.write({
                        'esito_invio': esito
                    })

            else:
                self.invio_trasmissione_segmentata_sequenziale(trasmissione, linee_trasmissione_json)

    def recupero_set_ordini_concorrente(self, codice_trasmissione, codice_cliente, trasmissione_id):
        try:
            token = get_valid_token()
            return {'trasmissione_id': trasmissione_id,
                    'codice_trasmissione': codice_trasmissione,
                    'codice_cliente': codice_cliente,
                    'response_recupero_ordini': receive_set_orders(token, codice_trasmissione)}
        except Exception as e:
            e.codice_trasmissione = codice_trasmissione
            e.codice_cliente = codice_cliente
            e.trasmissione_id = trasmissione_id
            raise e

    def cron_recupero_set_ordini(self):
        trasmissioni_in_elaborazione = self.search([('stato', '=', 'in_progress')])
        for trasmissione in trasmissioni_in_elaborazione:

            _logger.info(f"Recupero trasmissione: {trasmissione.id}, {trasmissione.descrizione}")

            totale_items = 0
            totale_valid = 0
            totale_toBeSent = 0
            totale_refused = 0
            totale_errors = 0
            new_state = 'in_progress'

            linee_da_elaborare = {}
            for linea_prenotazione in trasmissione.linee_trasmissione.gems_linea_prenotazione_id:
                if (linea_prenotazione.id_trasmissione and
                        linea_prenotazione.id_trasmissione not in linee_da_elaborare.values()):
                    linee_da_elaborare[linea_prenotazione] = linea_prenotazione.id_trasmissione

            results = []
            error_lines = {}  # linee in errore
            with ThreadPoolExecutor(max_workers=16) as executor:
                futures = {
                    executor.submit(self.recupero_set_ordini_concorrente, linea_prenotazione.id_trasmissione, linea_prenotazione.order_partner_id.gems_codice_azienda, trasmissione.id)
                    for linea_prenotazione in linee_da_elaborare.keys()}

                for future in as_completed(futures):
                    try:
                        results.append(future.result())
                        _logger.info(f"Risultato ottenuto: {future.result()}")
                    except Exception as e:
                        _logger.warning(f"Errore nel thread: {e}")
                        if hasattr(e, 'codice_trasmissione') and hasattr(e, 'codice_cliente') and hasattr(e, 'trasmissione_id'):
                            error_lines[(e.codice_trasmissione, e.codice_cliente, e.trasmissione_id)] = e
                        else:
                            pass

            for i in range(0, MAX_RETRIES):
                if error_lines:
                    _logger.warning(
                        f"Tentativo {i + 1}/{MAX_RETRIES} - Retry in corso per {len(error_lines)} linee fallite.")
                    new_error_lines = {}
                    with ThreadPoolExecutor(max_workers=16) as executor:
                        futures = {
                            executor.submit(self.recupero_set_ordini_concorrente, error[0], error[1], error[2])
                            for error in error_lines}

                        for future in as_completed(futures):
                            try:
                                results.append(future.result())
                                _logger.info(f"Risultato ottenuto: {future.result()}")
                            except Exception as e:
                                _logger.warning(f"Errore nel thread: {e}")
                                if hasattr(e, 'codice_trasmissione') and hasattr(e, 'codice_cliente') and hasattr(e, 'trasmissione_id'):
                                    new_error_lines[(e.codice_trasmissione, e.codice_cliente, e.trasmissione_id)] = e
                                else:
                                    pass
                    error_lines = new_error_lines

                    if error_lines and i < MAX_RETRIES - 1:
                        time.sleep(5)   # 5 secondi di attesa

            trasmissione_corrente = None

            if error_lines:
                _logger.error(f"{len(error_lines)} linee hanno fallito dopo {MAX_RETRIES} tentativi:")
                for error in error_lines:
                    _logger.error(f"errore {error_lines[error]} sulla linea: {error[0]}")
                    trasmissione_corrente = self.env['trasmissioni'].browse(error[2])
                    totale_errors += 1
            else:
                _logger.info("Tutte le linee recuperate correttamente.")

            self.env.cr.commit()

            valid_headers = True
            for res in results:
                trasmissione_corrente = self.env['trasmissioni'].browse(res['trasmissione_id'])
                linee_prenotazione = self.env['sale.order.line'].search([('id_trasmissione', '=', res['codice_trasmissione'])])

                linee_prenotazione.write({
                    'json_response': str(res['response_recupero_ordini'])
                })
                # _logger.info("RISPOSTA SET ORDINI:")
                # _logger.info(risposta_set_ordini)
                summary = []
                # Controlli

                for obj in res['response_recupero_ordini']:
                    # _logger.info("OBJ:")
                    # _logger.info(obj)
                    lista_items = obj['items']
                    # _logger.info("lista_items:")
                    # _logger.info(lista_items)
                    orderId = obj['header']['orderId']
                    # _logger.info("orderId:")
                    # _logger.info(orderId)
                    summary.append(obj['summary'])
                    # VIENE FATTA STA ZOZZERIA PER VIA DEGLI "0"(i) DAVANTI AL CODICE CLIENTI
                    if "code" in obj['header']['customer']:
                        customerCode = str(int(obj['header']['customer']['code']))
                    else:
                        # LISTA DI ERRORI, AD OGGI SOLO ARRAY CON UN SOLO ERRORE
                        # CONTROLLO SU obj['errors'][0]['propertyName' == "Header.CustomerCode" PER VERIFICARE IL CUSTOMER CODE
                        customerCode = str(int(obj['errors'][0]['propertyValue']))
                    for item in lista_items:
                        for linea_trasmissione in trasmissione_corrente.linee_trasmissione:
                            # Gestione lista items, controllo se l'ean della linea prenotazione è uguale all'ean della risposta
                            # _logger.info("controllo 1")
                            # _logger.info(item['title']['ean'] == linea_trasmissione.gems_ean)
                            # _logger.info("controllo 2")
                            # _logger.info(linea_trasmissione.gems_codice_cliente.gems_codice_azienda == customerCode)
                            if (item['title']['ean'] == linea_trasmissione.gems_ean and
                                    res['codice_cliente'] == customerCode):
                                # _logger.info("ITEM:")
                                # _logger.info(item)
                                if not item['acquired'] and "errors" in item:
                                    # Gestione errore specifico
                                    if item['errors'][0]['propertyDescription']:
                                        # _logger.info("SCRIVO item['errors'][0]['propertyDescription'] DENTRO motivo_inevaso:")
                                        # _logger.info(item['errors'][0]['propertyDescription'])
                                        # _logger.info("SCRIVO motivo_inevaso:")
                                        linea_trasmissione.write({
                                            'gems_motivo_anomalia': item['errors'][0]['propertyDescription'],
                                        })
                                # Controllo se il cliente della linea prenotazione è uguale al cliente della risposta
                                if res['codice_cliente'] == customerCode:
                                    # _logger.info("SCRIVO codice_ordine_trasmissione:")
                                    # _logger.info(orderId)
                                    linee_prenotazione.write({
                                        'codice_ordine_trasmissione': orderId,
                                    })
                                if not obj['acquired'] and "errors" in obj:
                                    # Gestione errore generico (livello cliente)
                                    # _logger.info("SCRIVO errore header:")
                                    # _logger.info(obj['errors'][0]['propertyDescription'])
                                    linee_prenotazione.write({
                                        'motivo_inevaso': obj['errors'][0]['propertyDescription'],
                                    })
                    if obj['acquired'] and obj['validated'] == "toBeSent":
                        valid_headers = False

                # CALCOLO DEL TOTALE PER ESITO TRASMISSIONE
                totale_summ_items = 0
                totale_summ_acquired = 0
                totale_summ_valid = 0
                totale_summ_toBeSent = 0
                totale_summ_refused = 0
                totale_summ_notValid = 0

                for summ in summary:
                    totale_summ_items += summ['items']
                    totale_summ_acquired += summ['acquired']
                    totale_summ_valid += summ['valid']
                    totale_summ_toBeSent += summ['toBeSent']
                    totale_summ_refused += summ['refused']
                    totale_summ_notValid += summ['notValid']

                totale_summ_items += totale_errors

                new_state = 'sale' if valid_headers else 'in_progress'
                esito_trasmissione = ('Totale Ordini: ' + str(totale_summ_items) +
                                      ' - Validati: ' + str(totale_summ_valid) +
                                      ' - In Validazione: ' + str(totale_summ_toBeSent) +
                                      ' - Rifiutati: ' + str(totale_summ_refused + totale_summ_notValid) +
                                      ' - In Errore: ' + str(totale_errors))

                esito_recupero = ""
                if totale_summ_valid:
                    esito_recupero = "valid"
                elif totale_summ_refused:
                    esito_recupero = "refused"
                elif totale_summ_toBeSent:
                    esito_recupero = "toBeSent"
                elif totale_summ_notValid:
                    esito_recupero = "notValid"

                linee_prenotazione.write({
                    'esito_recupero': esito_recupero,
                    'esito_trasmissione': esito_trasmissione,
                    'response_time': datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                })

                totale_items += totale_summ_items
                totale_valid += totale_summ_valid
                totale_toBeSent += totale_summ_toBeSent
                totale_refused += (totale_summ_refused + totale_summ_notValid)

            totale_esito = ('Totale Ordini: ' + str(totale_items) +
                            ' - Validati: ' + str(totale_valid) +
                            ' - In Validazione: ' + str(totale_toBeSent) +
                            ' - Rifiutati: ' + str(totale_refused) +
                            ' - In Errore: ' + str(totale_errors))
            trasmissione_corrente.write({
                'esito_recupero': totale_esito,
                'stato': new_state,
            })
            self.env.cr.commit()

    def action_modifica_trasmissione(self):
        form_view = self.env.ref('gestione_prenotazioni.modifica_trasmissioni_view_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Modifica Trasmissione',
            'res_model': 'trasmissioni',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(form_view.id, 'form')],
            'target': 'current',
        }

    def action_invio_modifica_trasmissione(self):
        modifica = False
        for linea_trasmissione in self.linee_trasmissione:
            for linea_prenotazione in linea_trasmissione.gems_linea_prenotazione_id:
                if (linea_prenotazione.qty_trasmessa != linea_prenotazione.qty_trasmessa_original or
                        linea_prenotazione.sconto_occasionale_trasmesso != linea_prenotazione.sconto_occasionale_trasmesso_original or
                        linea_prenotazione.termini_pagamento_occasionale_trasmesso != linea_prenotazione.termini_pagamento_occasionale_trasmesso_original or
                        linea_prenotazione.note_trasmissione != linea_prenotazione.note_trasmissione_original):

                    modifica = True
                    order_id = None
                    if linea_prenotazione.codice_ordine_trasmissione:
                        order_id = linea_prenotazione.codice_ordine_trasmissione
                    else:
                        linee_candidate = self.env['sale.order.line'].search([('id_trasmissione', '=', linea_prenotazione.id_trasmissione)])
                        for linea in linee_candidate:
                            if linea.codice_ordine_trasmissione:
                                order_id = linea.codice_ordine_trasmissione
                    ean = linea_prenotazione.ean

                    body = {
                        "NewBookedQuantity": linea_prenotazione.qty_trasmessa,
                        "NewOccasionalDiscountPercentage": linea_prenotazione.sconto_occasionale_trasmesso,
                        "NewTermsOfPaymentCode": linea_prenotazione.termini_pagamento_occasionale_trasmesso,
                        "NewItemNote": linea_prenotazione.note_trasmissione
                    }
                    _logger.info(f"order_id: {order_id}")
                    _logger.info(f"ean: {ean}")
                    _logger.info(f"body: {body}")
                    token = get_valid_token()
                    try:
                        response_data = update_orders(token, order_id, ean, body)
                        _logger.info(f"Modifica ordine riuscita per prenotazione {linea_prenotazione.id} - Risposta: {response_data}")
                        linea_prenotazione.write({'sconto_occasionale_trasmesso_original': linea_prenotazione.sconto_occasionale_trasmesso,
                                                  'termini_pagamento_occasionale_trasmesso_original': linea_prenotazione.termini_pagamento_occasionale_trasmesso,
                                                  'note_trasmissione_original': linea_prenotazione.note_trasmissione,
                                                  'codice_modifica_trasmissione': str(response_data)
                                                  })
                        new_value = linea_prenotazione.qty_trasmessa - linea_prenotazione.qty_trasmessa_original
                        linea_trasmissione.gems_totale_prenotazioni += new_value
                        linea_prenotazione.qty_trasmessa_original = linea_prenotazione.qty_trasmessa
                        self.stato = 'update'

                        form_view = self.env.ref('gestione_prenotazioni.trasmissioni_view_form')

                    except ValidationError as e:
                        _logger.error(f"Errore modifica ordine per prenotazione {linea_prenotazione.id}: {str(e)}")
                        raise ValidationError(f"Errore modifica ordine per prenotazione {linea_prenotazione.id}: {str(e)}")

        if modifica:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Trasmissioni',
                'view_mode': 'form',
                'res_model': 'trasmissioni',
                'target': 'current',
                'views': [(form_view.id, 'form')],
                'res_id': self.id,
            }
        else:
            raise UserError("Nessuna nuova modifica inserita!")

    def action_recupera_stato_modifica_trasmissione(self):
        lista_ean = []
        for record in self.linee_trasmissione:
            lista_ean.append(record.gems_product_template_id.id)

        stato_modifica_record = self.env['wizard.stato.modifica.trasmissione'].create([{
            'id_trasmissione': self.id,
            'ean_domain': lista_ean
        }])
        form_view = self.env.ref('gestione_prenotazioni.stato_modifica_trasmissioni_view_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stato Modifica Trasmissione',
            'res_model': 'wizard.stato.modifica.trasmissione',
            'res_id': stato_modifica_record.id,
            'view_mode': 'form',
            'views': [(form_view.id, 'form')],
            'target': 'current',
        }

    def action_invio_recupera_stato_modifica_trasmissione(self, id_trasmissione, titoli):
        trasmissione = self.search([('id', '=', id_trasmissione)])
        body = {}
        id_ean = {}
        id_cliente = {}
        if titoli:
            order_lines = []
            for linea_trasmissione in trasmissione.linee_trasmissione:
                for linea_prenotazione in linea_trasmissione.gems_linea_prenotazione_id:
                    if linea_prenotazione.product_template_id.id in titoli:
                        id_ean[linea_prenotazione.product_template_id.gems_ean] = linea_prenotazione.product_template_id.id
                        id_cliente[linea_prenotazione.codice_modifica_trasmissione] = linea_prenotazione.cliente.id
                        item = {}
                        if linea_prenotazione.codice_ordine_trasmissione:
                            item["OrderId"] = linea_prenotazione.codice_ordine_trasmissione
                            item["EanCode"] = linea_prenotazione.product_template_id.gems_ean
                        else:
                            linee_candidate = self.env['sale.order.line'].search([('id_trasmissione', '=', linea_prenotazione.id_trasmissione)])
                            for linea in linee_candidate:
                                if linea.codice_ordine_trasmissione:
                                    item["OrderId"] = linea.codice_ordine_trasmissione,
                                    item["EanCode"] = linea_prenotazione.product_template_id.gems_ean
                        order_lines.append(item)
            body["OrderLines"] = order_lines

        else:
            codici_modifica_trasmissione = []
            for linea_trasmissione in trasmissione.linee_trasmissione:
                for linea_prenotazione in linea_trasmissione.gems_linea_prenotazione_id:
                    if linea_prenotazione.codice_modifica_trasmissione:
                        id_ean[linea_prenotazione.product_template_id.gems_ean] = linea_prenotazione.product_template_id.id
                        id_cliente[linea_prenotazione.codice_modifica_trasmissione] = linea_prenotazione.cliente.id
                        codici_modifica_trasmissione.append(linea_prenotazione.codice_modifica_trasmissione)
            body["RequestChangeIds"] = codici_modifica_trasmissione

        _logger.info(f"body: {body}")

        _logger.info(f"id_ean: {id_ean}")

        _logger.info(f"id_cliente: {id_cliente}")

        _logger.info(f"body: {body}")

        token = get_valid_token()
        try:
            response_data = check_update_orders(token, body)
            _logger.info(f"response_data: {response_data}")
            _logger.info(f"Recupero stato modifica ordine riuscito per trasmissione {id_trasmissione} - Risposta: {response_data}")
            righe = response_data["rows"]
            records_da_creare = []
            for riga in righe:
                new_item = {
                    'trasmissione': trasmissione.descrizione,
                    'ean': id_ean[riga.get('eanCode')],
                    'cliente': id_cliente[str(riga.get('requestChangeId'))],
                    'qty': riga.get('bookedQuantity', False),
                    'sconto': riga.get('occasionalDiscountPercentage', False),
                    'termini_pagamento': riga.get('termsOfPaymentCode', False),
                    'note': riga.get('itemNote', False),
                    'new_qty': riga.get('newBookedQuantity'),
                    'new_sconto': riga.get('newOccasionalDiscountPercentage'),
                    'new_termini_pagamento': riga.get('newTermsOfPaymentCode'),
                    'new_note': riga.get('newItemNote'),
                    'stato': riga.get('status'),
                    'data_tentativo': datetime.strptime(riga.get('sapChangeDate').replace("T", " "), "%Y-%m-%d %H:%M:%S"),
                    'motivo_fallimento': riga.get('sapReasonNotChange', False)
                }
                records_da_creare.append(new_item)
                _logger.info(f"records_da_creare: {records_da_creare}")

            stato_modifica_record = self.env['wizard.stato.modifica.trasmissione'].create(records_da_creare)
            return stato_modifica_record

        except ValidationError as e:
            _logger.error(f"Errore recupero stato modifica ordine per trasmissione {id_trasmissione}: {str(e)}")
            raise ValidationError(f"Errore recupero stato modifica ordine per trasmissione {id_trasmissione}: {str(e)}")

    def action_riepilogo_trasmissione(self):
        recordset = self.env['sale.order.line'].search([('gems_linee_trasmissione_id.gems_trasmissione_id', '=', self.id)])
        _logger.info(f"recordset: {recordset}")
        action = self.env.ref('gestione_prenotazioni.action_riepilogo_trasmissione').read()[0]
        action['domain'] = [('id', 'in', recordset.ids)]
        return action