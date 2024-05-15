from odoo import fields, models, api, _
import base64
import datetime
import io


class ShMYOBWizard(models.TransientModel):
    _name = 'sh.myob.wizard'
    _description = 'MYOB Wizard'

    def _default_start_date(self):
        """ Find the earliest start_date of the latest sessions """
        return fields.Datetime.now()

    start_date = fields.Date(required=True, default=_default_start_date)
    end_date = fields.Date(required=True, default=fields.Datetime.now)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

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

        self._cr.execute('''SELECT CASE WHEN "Allocation Memo" IS NULL THEN NULL ELSE "Date" END "Date",
	   "Allocation Memo",
	   "GST [BAS] Reporting",
	   "Account Number",
	   "Debit Ex-Tax Amount",
	   "Debit Inc-Tax Amount",
	   "Credit Ex-Tax Amount",
	   "Credit Inc-Tax Amount",
	   "Tax Code"
FROM(
SELECT * FROM (
	-- Prepare Ledger
	SELECT "Date",
		   "Sequence",
		   "Allocation Memo",
		   "GST [BAS] Reporting",
		   "Account Number",
		   CASE WHEN "SUM" > 0 THEN "SUM" ELSE NULL END "Debit Ex-Tax Amount",
		   CASE WHEN "SUM" > 0 THEN "SUM" ELSE NULL END "Debit Inc-Tax Amount",
		   CASE WHEN "SUM" < 0 THEN "SUM" * -1 ELSE NULL END "Credit Ex-Tax Amount",
		   CASE WHEN "SUM" < 0 THEN "SUM" * -1 ELSE NULL END "Credit Inc-Tax Amount",
		   "Tax Code"
	FROM (
		-- Cash/Cheque Receipts
		SELECT 1 "Sequence",
			   account_move_line.company_id,
			   account_move_line.date "Date",
			   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Cash/Cheque Receipts') "Allocation Memo",
			   'S' "GST [BAS] Reporting",
			   CASE WHEN account_move_line.company_id = 6 THEN 11120
					WHEN account_move_line.company_id = 9 THEN 11120
					ELSE NULL END "Account Number",
			   ROUND(SUM(account_move_line.balance), 2) "SUM",
			   'N-T' "Tax Code"
		FROM public.account_move_line
		JOIN public.account_account ON account_move_line.account_id = account_account.id
		WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'CSH1/%%' AND account_account.code = '11131' AND account_move_line.name NOT LIKE 'Opening%%'
		GROUP BY account_move_line.company_id, "Date"

		UNION ALL

		-- EFTPOS Receipts
		SELECT 2 "Sequence",
			   account_move_line.company_id,
			   account_move_line.date "Date",
			   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'EFTPOS Receipts') "Allocation Memo",
			   'S' "GST [BAS] Reporting",
			   CASE WHEN account_move_line.company_id = 6 THEN 11150
					WHEN account_move_line.company_id = 9 THEN 11190
					ELSE NULL END "Account Number",
			   ROUND(SUM(account_move_line.balance), 2) "SUM",
			   'N-T' "Tax Code"
		FROM public.account_move_line
		JOIN public.account_account ON account_move_line.account_id = account_account.id
		WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'EFT/%%' AND account_account.code = '11112' 
		GROUP BY account_move_line.company_id, "Date"

		UNION ALL

		-- Reward Vouchers
		SELECT 3 "Sequence",
			   account_move_line.company_id,
			   account_move_line.date "Date",
			   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Reward Vouchers') "Allocation Memo",
			   'S' "GST [BAS] Reporting",
			   CASE WHEN account_move_line.company_id = 6 THEN 11208
					WHEN account_move_line.company_id = 9 THEN 11170
					ELSE NULL END "Account Number",
			   ROUND(SUM(account_move_line.balance), 2) "SUM",
			   'N-T' "Tax Code"
		FROM public.account_move_line
		JOIN public.account_account ON account_move_line.account_id = account_account.id
		WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'INV/%%' AND account_move_line.name LIKE '%%Loyalty' 
		GROUP BY account_move_line.company_id, "Date"

		UNION ALL

		-- Staff Amenities
		SELECT 4 "Sequence",
			   account_move_line.company_id,
			   account_move_line.date "Date",
			   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Staff Amenities') "Allocation Memo",
			   'S' "GST [BAS] Reporting",
			   CASE WHEN account_move_line.company_id = 6 THEN 11140
					WHEN account_move_line.company_id = 9 THEN 11140
					ELSE NULL END "Account Number",
			   ROUND(SUM(account_move_line.balance), 2) "SUM",
			   'N-T' "Tax Code"
		FROM public.account_move_line
		JOIN public.account_account ON account_move_line.account_id = account_account.id
		WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'CSH1/%%' AND account_account.code = '11111' AND account_move_line.name NOT LIKE 'Opening%%'
		GROUP BY account_move_line.company_id, "Date"

		UNION ALL

		-- Till Shortage
		SELECT 5 "Sequence",
			   account_move_line.company_id,
			   account_move_line.date "Date",
			   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Till Shortage') "Allocation Memo",
			   'S' "GST [BAS] Reporting",
			   CASE WHEN account_move_line.company_id = 6 THEN 67503
					WHEN account_move_line.company_id = 9 THEN 67503
					ELSE NULL END "Account Number",
			   ROUND(SUM(account_move_line.balance), 2) "SUM",
			   'N-T' "Tax Code"
		FROM public.account_move_line
		JOIN public.account_account ON account_move_line.account_id = account_account.id
		WHERE account_move_line.create_uid <> 2 AND account_account.code IN ('99901', '99902') AND (account_move_line.move_name LIKE 'CSH1/%%' OR account_move_line.move_name LIKE 'EFT/%%')
		GROUP BY account_move_line.company_id, "Date"

		UNION ALL
		
		-- Sales With GST
		SELECT "Sequence",
			   company_id,
			   "Date",
			   "Allocation Memo",
			   "GST [BAS] Reporting",
			   "Account Number",
			   SUM("SUM") "SUM",
			   "Tax Code"
		FROM (
			-- Sales With GST 1
			SELECT 6 "Sequence",
				   account_move_line.company_id,
				   account_move_line.date "Date",
				   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Sales With GST') "Allocation Memo",
				   'S' "GST [BAS] Reporting",
				   CASE WHEN account_move_line.company_id = 6 THEN 41001
						WHEN account_move_line.company_id = 9 THEN 41001
						ELSE NULL END "Account Number",
				   ROUND(SUM(account_move_line.price_total * -1), 2) "SUM",
				   'GST' "Tax Code"
			FROM public.account_move_line
			JOIN public.account_account ON account_move_line.account_id = account_account.id
			WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'INV/%%' AND account_move_line.name LIKE 'Sales with%%'
			GROUP BY account_move_line.company_id, "Date"

			UNION ALL

			-- Sales With GST 2
			SELECT 6 "Sequence",
				   account_move_line.company_id,
				   account_move_line.date "Date",
				   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Sales With GST') "Allocation Memo",
				   'S' "GST [BAS] Reporting",
				   CASE WHEN account_move_line.company_id = 6 THEN 41001
						WHEN account_move_line.company_id = 9 THEN 41001
						ELSE NULL END "Account Number",
				   ROUND(SUM(account_move_line.balance), 2) "SUM",
				   'GST' "Tax Code"
			FROM public.account_move_line
			JOIN public.account_account ON account_move_line.account_id = account_account.id
			WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'INV/%%' AND account_move_line.name IS NULL AND account_account.code = '11200'
			GROUP BY account_move_line.company_id, "Date"
		
			UNION ALL

			-- Sales With GST 3
			SELECT 6 "Sequence",
				   account_move_line.company_id,
				   account_move_line.date "Date",
				   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Sales With GST') "Allocation Memo",
				   'S' "GST [BAS] Reporting",
				   CASE WHEN account_move_line.company_id = 6 THEN 41001
						WHEN account_move_line.company_id = 9 THEN 41001
						ELSE NULL END "Account Number",
				   ROUND(SUM(account_move_line.balance), 2) "SUM",
				   'GST' "Tax Code"
			FROM public.account_move_line
			JOIN public.account_account ON account_move_line.account_id = account_account.id
			WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'INV/%%' AND account_move_line.name LIKE 'Difference%%'
			GROUP BY account_move_line.company_id, "Date") GSTSALES
		GROUP BY "Sequence",
			     company_id,
			     "Date",
			     "Allocation Memo",
			     "GST [BAS] Reporting",
			     "Account Number",
			     "Tax Code"

		UNION ALL

		-- Sales GST Free
		SELECT 7 "Sequence",
			   account_move_line.company_id,
			   account_move_line.date "Date",
			   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Sales GST Free') "Allocation Memo",
			   'S' "GST [BAS] Reporting",
			   CASE WHEN account_move_line.company_id = 6 THEN 41001
					WHEN account_move_line.company_id = 9 THEN 41001
					ELSE NULL END "Account Number",
			   ROUND(SUM(account_move_line.price_total * -1), 2) "SUM",
			   'FRE' "Tax Code"
		FROM public.account_move_line
		JOIN public.account_account ON account_move_line.account_id = account_account.id
		WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'INV/%%' AND account_move_line.name LIKE 'Sales untaxed%%' 
		GROUP BY account_move_line.company_id, "Date"

		UNION ALL

		-- Sales Rounding
		SELECT 8 "Sequence",
			   account_move_line.company_id,
			   account_move_line.date "Date",
			   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Sales Rounding') "Allocation Memo",
			   'S' "GST [BAS] Reporting",
			   CASE WHEN account_move_line.company_id = 6 THEN 41001
					WHEN account_move_line.company_id = 9 THEN 41001
					ELSE NULL END "Account Number",
			   ROUND(SUM(account_move_line.balance), 2) "SUM",
			   'GST' "Tax Code"
		FROM public.account_move_line
		JOIN public.account_account ON account_move_line.account_id = account_account.id
		WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'INV/%%' AND account_move_line.name LIKE 'Rounding line%%' 
		GROUP BY account_move_line.company_id, "Date"

		UNION ALL

		-- Refunds With GST
		SELECT 9 "Sequence",
			   account_move_line.company_id,
			   account_move_line.date "Date",
			   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Refunds With GST') "Allocation Memo",
			   'S' "GST [BAS] Reporting",
			   CASE WHEN account_move_line.company_id = 6 THEN 41001
					WHEN account_move_line.company_id = 9 THEN 41001
					ELSE NULL END "Account Number",
			   ROUND(SUM(account_move_line.price_total), 2) "SUM",
			   'GST' "Tax Code"
		FROM public.account_move_line
		JOIN public.account_account ON account_move_line.account_id = account_account.id
		WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'INV/%%' AND account_move_line.name LIKE 'Refund with%%' 
		GROUP BY account_move_line.company_id, "Date"

		UNION ALL

		-- Refunds GST Free
		SELECT 10 "Sequence",
			   account_move_line.company_id,
			   account_move_line.date "Date",
			   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Refunds GST Free') "Allocation Memo",
			   'S' "GST [BAS] Reporting",
			   CASE WHEN account_move_line.company_id = 6 THEN 41001
					WHEN account_move_line.company_id = 9 THEN 41001
					ELSE NULL END "Account Number",
			   ROUND(SUM(account_move_line.price_total), 2) "SUM",
			   'FRE' "Tax Code"
		FROM public.account_move_line
		JOIN public.account_account ON account_move_line.account_id = account_account.id
		WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'INV/%%' AND account_move_line.name LIKE 'Refund untaxed%%' 
		GROUP BY account_move_line.company_id, "Date"

		UNION ALL

		-- Cost of Goods Sold
		SELECT 11 "Sequence",
			   account_move_line.company_id,
			   account_move_line.date "Date",
			   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Cost of Goods Sold') "Allocation Memo",
			   'S' "GST [BAS] Reporting",
			   CASE WHEN account_move_line.company_id = 6 THEN 52010
					WHEN account_move_line.company_id = 9 THEN 52010
					ELSE NULL END "Account Number",
			   ROUND(SUM(account_move_line.balance), 2) "SUM",
			   'N-T' "Tax Code"
		FROM public.account_move_line
		JOIN public.account_account ON account_move_line.account_id = account_account.id
		WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'STJ/%%' AND account_move_line.name LIKE 'Go Vi/POS%%' AND account_account.code = '51110'
		GROUP BY account_move_line.company_id, "Date"

		UNION ALL

		-- Inventory
		SELECT 12 "Sequence",
			   account_move_line.company_id,
			   account_move_line.date "Date",
			   CONCAT(to_char(account_move_line.date, 'DD/MM/YYYY'), ' ', 'Inventory') "Allocation Memo",
			   'S' "GST [BAS] Reporting",
			   CASE WHEN account_move_line.company_id = 6 THEN 11300
					WHEN account_move_line.company_id = 9 THEN 11300
					ELSE NULL END "Account Number",
			   ROUND(SUM(account_move_line.balance), 2) "SUM",
			   'N-T' "Tax Code"
		FROM public.account_move_line
		JOIN public.account_account ON account_move_line.account_id = account_account.id
		WHERE account_move_line.create_uid <> 2 AND account_move_line.move_name LIKE 'STJ/%%' AND account_move_line.name LIKE 'Go Vi/POS%%' AND account_account.code = '11330'
		GROUP BY account_move_line.company_id, "Date") MAIN	
	WHERE company_id = %s AND "Date" BETWEEN '%s' AND '%s'

	UNION ALL

	SELECT DISTINCT account_move_line.date "Date",
		   NULL::int,
		   NULL,
		   NULL,
		   NULL::int,
		   NULL::int,
		   NULL::int,
		   NULL::int,
		   NULL::int,
		   NULL
	FROM public.account_move_line
	JOIN public.account_account ON account_move_line.account_id = account_account.id
	WHERE account_move_line.company_id = %s AND account_move_line.date BETWEEN '%s' AND '%s'
	GROUP BY "Date" OFFSET 0)ADDSPACE ORDER BY "Date", "Sequence" NULLS LAST) REMOVEDATE''' % (company_id, start_date, end_date, company_id, start_date, end_date))

        rows = self._cr.fetchall()
        filename = 'MYOB General (' + str(company_name) + ') (' + str(start_date) + ' - ' + str(end_date) + ').txt'
        
        # Open a new text file to write
        output = io.StringIO()
        
        # Write the header row
        headers = ["Date", "Allocation Memo", "GST [BAS] Reporting", "Account Number", "Debit Ex-Tax Amount", "Debit Inc-Tax Amount", "Credit Ex-Tax Amount", "Credit Inc-Tax Amount", "Tax Code"]
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
