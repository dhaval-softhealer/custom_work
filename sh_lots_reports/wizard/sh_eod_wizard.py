# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models,api,_
import base64
import xlwt
import datetime
import io

class EodreportWizard(models.TransientModel):
    _name = 'sh.eod.wizard'
    _description = 'EOD Wizard'

    start_date = fields.Date(required=True, default=fields.Datetime.now())
    end_date = fields.Date(required=True, default=fields.Datetime.now)

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.end_date = self.start_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.end_date < self.start_date:
            self.start_date = self.end_date

    def print_report(self):
        self._cr.execute('''SELECT res_company.name "Company",
       pos_config.name "Till Name",
       (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE "Date",
       opening.start_at AT time zone 'UTC' AT time zone 'ACST' "Opened",
       opening.balance_start "Opening Balance",
       closing.stop_at  AT time zone 'UTC' AT time zone 'ACST' "Closed",
       closing.balance_end_real "Closing Balance",
       SUM(CASE WHEN LOWER(pos_payment_method.name) = 'cash' THEN pos_payment.amount ELSE 0 END) "Cash",
       SUM(CASE WHEN LOWER(pos_payment_method.name) = 'eftpos' THEN pos_payment.amount ELSE 0 END) "EFTPOS",
       SUM(CASE WHEN LOWER(pos_payment_method.name) = 'loyalty' THEN pos_payment.amount ELSE 0 END) "Loyalty",
       CASE WHEN cash_in_out.amount IS NULL THEN 0 ELSE cash_in_out.amount END "Cash In/Out" 
FROM public.res_company
JOIN public.pos_config ON res_company.id = pos_config.company_id
JOIN public.pos_session ON pos_config.id = pos_session.config_id
JOIN public.pos_payment ON pos_session.id = pos_payment.session_id
JOIN public.pos_payment_method ON pos_payment.payment_method_id = pos_payment_method.id
LEFT JOIN (SELECT * 
        FROM (SELECT config_id, (start_at AT time zone 'UTC' AT time zone 'ACST')::DATE "date", start_at, balance_start,
                     ROW_NUMBER() OVER (PARTITION BY pos_session.config_id, (start_at AT time zone 'UTC' AT time zone 'ACST')::DATE ORDER BY start_at ASC) AS r
                FROM public.pos_session
                JOIN public.account_bank_statement ON pos_session.id = account_bank_statement.pos_session_id) x
       WHERE x.r = 1) opening ON pos_session.config_id = opening.config_id AND (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE = opening.date                      
LEFT JOIN (SELECT * 
        FROM (SELECT config_id, (start_at AT time zone 'UTC' AT time zone 'ACST')::DATE "date", stop_at, balance_end_real,
                     ROW_NUMBER() OVER (PARTITION BY pos_session.config_id, (start_at AT time zone 'UTC' AT time zone 'ACST')::DATE ORDER BY stop_at DESC) AS r
                FROM public.pos_session
                JOIN public.account_bank_statement ON pos_session.id = account_bank_statement.pos_session_id) x
       WHERE x.r = 1) closing ON pos_session.config_id = closing.config_id AND (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE = closing.date
LEFT JOIN (SELECT config_id,
                  (start_at AT time zone 'UTC' AT time zone 'ACST')::DATE "date",
                  SUM(CASE WHEN sh_transaction_type = 'cash_in' THEN sh_amount
                           WHEN sh_transaction_type = 'cash_out' THEN sh_amount * -1 ELSE 0 END) "amount"
             FROM public.sh_cash_in_out
             JOIN public.pos_session ON sh_cash_in_out.sh_session = pos_session.id
             GROUP BY (start_at AT time zone 'UTC' AT time zone 'ACST')::DATE,
                      config_id) cash_in_out ON pos_session.config_id = cash_in_out.config_id
                                             AND (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE = cash_in_out.date
WHERE (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE >= '%s' AND (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE <= '%s'                                             
GROUP BY res_company.name,
         pos_config.name,
         (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE,
         Opening.start_at AT time zone 'UTC' AT time zone 'ACST',
         Opening.balance_start,
         closing.stop_at AT time zone 'UTC' AT time zone 'ACST',
         closing.balance_end_real,
         cash_in_out.amount
--ORDER BY (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE DESC

UNION ALL

SELECT 'TOTAL',
       NULL,
       NULL,
       NULL,
       NULL,
       NULL,
       NULL,
       SUM(CASE WHEN LOWER(pos_payment_method.name) = 'cash' THEN pos_payment.amount ELSE 0 END) "Cash",
       SUM(CASE WHEN LOWER(pos_payment_method.name) = 'eftpos' THEN pos_payment.amount ELSE 0 END) "EFTPOS",
       SUM(CASE WHEN LOWER(pos_payment_method.name) = 'loyalty' THEN pos_payment.amount ELSE 0 END) "Loyalty",
       NULL
FROM public.res_company
JOIN public.pos_config ON res_company.id = pos_config.company_id
JOIN public.pos_session ON pos_config.id = pos_session.config_id
JOIN public.pos_payment ON pos_session.id = pos_payment.session_id
JOIN public.pos_payment_method ON pos_payment.payment_method_id = pos_payment_method.id
LEFT JOIN (SELECT * 
        FROM (SELECT config_id, (start_at AT time zone 'UTC' AT time zone 'ACST')::DATE "date", start_at, balance_start,
                     ROW_NUMBER() OVER (PARTITION BY pos_session.config_id, (start_at AT time zone 'UTC' AT time zone 'ACST')::DATE ORDER BY start_at ASC) AS r
                FROM public.pos_session
                JOIN public.account_bank_statement ON pos_session.id = account_bank_statement.pos_session_id) x
       WHERE x.r = 1) opening ON pos_session.config_id = opening.config_id AND (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE = opening.date                      
LEFT JOIN (SELECT * 
        FROM (SELECT config_id, (start_at AT time zone 'UTC' AT time zone 'ACST')::DATE "date", stop_at, balance_end_real,
                     ROW_NUMBER() OVER (PARTITION BY pos_session.config_id, (start_at AT time zone 'UTC' AT time zone 'ACST')::DATE ORDER BY stop_at DESC) AS r
                FROM public.pos_session
                JOIN public.account_bank_statement ON pos_session.id = account_bank_statement.pos_session_id) x
       WHERE x.r = 1) closing ON pos_session.config_id = closing.config_id AND (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE = closing.date
LEFT JOIN (SELECT config_id,
                  (start_at AT time zone 'UTC' AT time zone 'ACST')::DATE "date",
                  SUM(CASE WHEN sh_transaction_type = 'cash_in' THEN sh_amount
                           WHEN sh_transaction_type = 'cash_out' THEN sh_amount * -1 ELSE 0 END) "amount"
             FROM public.sh_cash_in_out
             JOIN public.pos_session ON sh_cash_in_out.sh_session = pos_session.id
             GROUP BY (start_at AT time zone 'UTC' AT time zone 'ACST')::DATE,
                      config_id) cash_in_out ON pos_session.config_id = cash_in_out.config_id
                                             AND (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE = cash_in_out.date
WHERE (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE >= '%s' AND (pos_session.start_at AT time zone 'UTC' AT time zone 'ACST')::DATE <= '%s'                                             
ORDER BY "Date" ASC''' %(self.start_date,self.end_date,self.start_date,self.end_date))


        rows = self._cr.fetchall()
        filename = 'EOD Report.xls'
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        normal_text = xlwt.easyxf(
                'font:bold False,color black;align: horiz center;align: vert center;')
        bold_text = xlwt.easyxf(
        'font:bold True,color black;align: horiz center;align: vert center;pattern: pattern solid,fore_colour gray25;')
        worksheet.write(0, 0, "Company", bold_text)
        worksheet.write(0, 1, "Till Name", bold_text)
        worksheet.write(0, 2, "Date", bold_text)
        worksheet.write(0, 3, "Opened", bold_text)
        worksheet.write(0, 4, "Opening Balance", bold_text)
        worksheet.write(0, 5, "Closed", bold_text)
        worksheet.write(0, 6, "Closing Balance", bold_text)
        worksheet.write(0, 7, "Cash", bold_text)
        worksheet.write(0, 8, "EFTPOS", bold_text)
        worksheet.write(0, 9, "Loyalty", bold_text)
        worksheet.write(0, 10, "Cash In/Out", bold_text)
        if rows:
            row = 0            
            for record in rows:
                row += 1
                col = 0
                for value in record:
                    if type(value) is datetime.datetime:
                        worksheet.write(row, col, value.strftime('%d-%m-%Y %H:%M:%S'), normal_text)
                    elif type(value) is datetime.date:
                        worksheet.write(row, col, value.strftime('%x'), normal_text)
                    else:
                        worksheet.write(row, col, value, normal_text)
                    col += 1
        fp = io.BytesIO()
        workbook.save(fp)
        attachment_id = self.env['ir.attachment'].create({'name': 'Data File',
                                                            'datas':  base64.encodebytes(fp.getvalue()),
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

    def on_screen_report(self):        
        self.ensure_one()
        ctx = self.env.context
        ctx = dict(ctx)
        ctx.update({
            'start_date':self.start_date,
            'end_date':self.end_date,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'sh_eod_report.report',
            'context':ctx,          
        }