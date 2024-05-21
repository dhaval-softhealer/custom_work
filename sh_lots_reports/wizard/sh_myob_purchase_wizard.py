from odoo import fields, models, api, _
import base64
import datetime
import io


class ShMYOBPurchaseWizard(models.TransientModel):
    _name = 'sh.myob.purchase.wizard'
    _description = 'MYOB Purchase Wizard'

    def _default_start_date(self):
        """ Find the earliest start_date of the latest sessions """
        return fields.Datetime.now()

    start_date = fields.Date(required=True, default=_default_start_date)
    end_date = fields.Date(required=True, default=fields.Datetime.now)
    def _default_domain(self):
        return [('id','in',self.env.user.company_ids.ids)]
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company ,  domain=_default_domain)

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.end_date = self.start_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.end_date < self.start_date:
            self.start_date = self.end_date

    def print_report(self):
        datas = self.read()[0]
        company_id = datas['company_id'][0]
        company_name = self.company_id.name
        start_date = str(datas['start_date'])
        end_date = str(datas['end_date'])

        self._cr.execute('''SELECT "Co./Last Name",
	   "Date",
	   "Account #",
	   "Supplier Invoice #",
	   CASE WHEN "Date" IS NULL THEN NULL ELSE "Description" END "Description",
	   "Amount",
	   "Inc-Tax Amount",
	   "GST Amount",
	   "Tax Code"
FROM(
SELECT * FROM(
SELECT account_move.invoice_partner_display_name "Co./Last Name",
	   account_move.invoice_date "Date",
	   11300 "Account #",
	   account_move.ref "Supplier Invoice #",
	   account_move.name "Description",
	   CASE WHEN account_move.name LIKE 'BILL%%' THEN SUM(account_move_line.price_subtotal)
	   		ELSE SUM(account_move_line.price_subtotal) * -1 END "Amount",
	   CASE WHEN account_move.name LIKE 'BILL%%' THEN SUM(account_move_line.price_total)
	   		ELSE SUM(account_move_line.price_total) * -1 END "Inc-Tax Amount",
	   CASE WHEN account_move.name LIKE 'BILL%%' THEN SUM(account_move_line.price_total - account_move_line.price_subtotal)
	   		ELSE SUM(account_move_line.price_total - account_move_line.price_subtotal) * -1 END "GST Amount",
	   CASE WHEN tax_audit = '' THEN 'FRE' ELSE 'GST' END "Tax Code"

FROM public.account_move
JOIN public.account_move_line ON account_move.id = account_move_line.move_id
WHERE account_move.state = 'posted'
AND (account_move.name LIKE 'BILL%%' OR account_move.name LIKE 'RBILL%%' OR invoice_origin LIKE 'S%%')
AND account_move.company_id = %s
AND account_move.date BETWEEN '%s' AND '%s'
AND product_id IS NOT NULL
GROUP BY account_move.invoice_partner_display_name,
		 account_move.invoice_date,
		 account_move.ref,
		 account_move.name,
		 CASE WHEN tax_audit = '' THEN 'FRE' ELSE 'GST' END

UNION ALL

SELECT NULL,
       NULL,
       NULL,
       NULL,
       account_move.name "Description",
       NULL,
       NULL,
       NULL,
       NULL      
FROM public.account_move
LEFT JOIN public.account_move_line ON account_move.id = account_move_line.move_id
WHERE account_move.state = 'posted'
AND (account_move.name LIKE 'BILL%%' OR account_move.name LIKE 'RBILL%%' OR invoice_origin LIKE 'S%%')
AND account_move.company_id = %s
AND account_move.date BETWEEN '%s' AND '%s'
AND product_id IS NOT NULL
GROUP BY "Description" OFFSET 0)addspace
ORDER BY "Description", "Tax Code" NULLS LAST) removedate''' % (company_id, start_date, end_date, company_id, start_date, end_date))

        rows = self._cr.fetchall()
        filename = 'MYOB Purchase (' + str(company_name) + ') (' + str(start_date) + ' - ' + str(end_date) + ').txt'
        
        # Open a new text file to write
        output = io.StringIO()
        
        # Write the header row
        headers = ["Co./Last Name", "Date", "Account #", "Supplier Invoice #", "Description", "Amount", "Inc-Tax Amount", "GST Amount", "Tax Code"]
        output.write('\t'.join(headers) + '\n')
        
        # Write data rows
        for record in rows:
            row_data = []
            for value in record:
                if value is None:
                    formatted_value = ""
                elif isinstance(value, datetime.datetime):
                    formatted_value = value.strftime('%d/%m/%Y %H:%M:%S')
                elif isinstance(value, datetime.date):
                    formatted_value = value.strftime('%d/%m/%Y')
                else:
                    formatted_value = str(value)
                row_data.append(formatted_value)
            output.write('\t'.join(row_data) + '\n')

        # Seek to the start of the StringIO object
        output.seek(0)
        
        # Encode the StringIO contents to binary
        file_data = output.getvalue().encode()
        output.close()

        # Create attachment
        attachment_id = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.encodebytes(file_data),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary'
        })
        attachment_url = '/web/content/' + str(attachment_id.id) + '?download=true&filename='+ filename
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': attachment_url,
        }
