# Copyright (C) Softhealer Technologies.

from odoo import http
from odoo.http import request
import json


class EodReport(http.Controller):

    # Sale Attribute Report
    @http.route('/sh_get_eod_report', type='http', auth="public", methods=['GET'])
    def sh_get_eod_report(self, **post):
        if post:
            # Get Fields value which is selected in wizard 
            context_action=json.loads(post['context[_originalAction]'])
            start_date=context_action['context']['start_date']
            end_date=context_action['context']['end_date']
            
            request._cr.execute('''SELECT res_company.name "Company",
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
ORDER BY "Date" ASC''' %(start_date,end_date,start_date,end_date))


            rows = request._cr.fetchall()
            headers = ['Company','Till Name','Date','Opened','Opening Balance','Closed','Closing Balance','Cash', 'EFTPOS', 'Loyalty', 'Cash In/Out']
            # Return Prepare data to Display Report
            if rows:
                return request.env['ir.ui.view'].with_context()._render_template('sh_lots_reports.sh_eod_report_tbl', 
                {   'rows' : rows,
                    'headers' : headers
                })
            else:
                return request.env['ir.ui.view'].with_context()._render_template('sh_lots_reports.sh_eod_no_report_tbl')
