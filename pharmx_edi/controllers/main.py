from odoo.addons.web.controllers.main import DataSet
from odoo.http import request, route


class CustomDataSet(DataSet):

    @route()
    def search_read(self, model, fields=False, offset=0, limit=False, domain=None, sort=None):
        return self.do_search_read(model, fields, offset, limit, domain, sort)

    def do_search_read(self, model, fields=False, offset=0, limit=False, domain=None, sort=None):
        Model = request.env[model]

        records = Model.search_read(domain, fields, offset=offset or 0, limit=limit or False, order=sort or False)
        if not records:
            return {
                'length': 0,
                'records': []
            }
        
        length = -1
        if len(domain) == 0:
            # taken from https://www.cybertec-postgresql.com/en/postgresql-count-made-fast/
            request.env.cr.execute('SELECT reltuples::bigint FROM pg_catalog.pg_class WHERE relname = %s', (Model._table,))
            z = request.env.cr.fetchone()
            if len(z) > 0:
                length = z[0]
        if length == -1:
            if limit and len(records) == limit:
                length = Model.search_count(domain)
            else:
                length = len(records) + (offset or 0)
        return {
            'length': 0,
            'records': records
        }