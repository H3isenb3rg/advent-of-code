for order in records:
    partner = order.partner_id

    # 0) Read max sequence currently on the SO
    conai_seq = max(line.sequence or 0 for line in order.order_line) + 10

    # 1) All CONAI products affected in this order
    affected_conai_product_ids = set()
    for line in order.order_line:
        tmpl = line.product_id.product_tmpl_id
        for contrib in tmpl.x_studio_contributi_conai:
            affected_conai_product_ids.add(
                contrib.x_studio_conai_product_id.product_variant_id.id
            )

    # 2) For each affected CONAI product, recompute total qty based on all lines
    for conai_product_id in affected_conai_product_ids:
        total_qty = 0.0

        for line in order.order_line:
            tmpl2 = line.product_id.product_tmpl_id
            for contrib2 in tmpl2.x_studio_contributi_conai:
                if contrib2.x_studio_conai_product_id.product_variant_id.id == conai_product_id:
                    total_qty += (
                        tmpl2.x_studio_peso_conai
                        * contrib2.x_studio_contributo
                        * line.product_qty
                    )

        # 2.b) Apply partner "esenzione CONAI" if configured
        if partner:
            conai_product = order.env['product.product'].browse(conai_product_id)
            conai_tmpl = conai_product.product_tmpl_id

            esenzione_line = partner.x_studio_esenzioni_conai.filtered(
                lambda e: e.x_studio_conai_product_id.id == conai_tmpl.id
            )[:1]

            if esenzione_line:
                total_qty = total_qty * esenzione_line.x_studio_esenzione

        # 3) Update existing CONAI line or create a new one
        existing_line = order.order_line.filtered(
            lambda l: l.product_id.id == conai_product_id
        )[:1]

        if total_qty == 0.0:
            if existing_line and existing_line.product_id.categ_id.x_studio_is_conai:
                existing_line.unlink()
        else:
            if existing_line:
                existing_line.write({'product_uom_qty': total_qty, 'sequence': conai_seq})
            else:
                order.env['sale.order.line'].create({
                    'order_id': order.id,
                    'product_id': conai_product_id,
                    'product_uom_qty': total_qty,
                    'sequence': conai_seq,
                })

    # 4) Delete CONAI lines that exist but are not needed anymore
    order.order_line.filtered(
        lambda l: l.product_id.categ_id.x_studio_is_conai
        and l.product_id.id not in affected_conai_product_ids
    ).unlink()

    order.message_post(
        body="CONAI Aggiornato",
        message_type="comment",
        subtype_xmlid="mail.mt_note",  # log note
    )
