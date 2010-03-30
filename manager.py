from IPy import IP

from django.core.exceptions import ValidationError
from django.db import models, connection
from django.db.models import sql, query

INET_TERMS = {
    'inet_lt': '<',
    'inet_lte': '<=',
    'inet_exact': '=',
    'inet_gte': '>=',
    'inet_gt': '>',
    'inet_not': '<>',
    'inet_is_contained': '<<',
    'inet_is_contained_or_equal': '<<=',
    'inet_contains': '>>',
    'inet_contains': '>>=',
}

class IPQuery(sql.Query):
    query_terms = sql.Query.query_terms.copy()
    query_terms.update(INET_TERMS)

class IPWhere(sql.where.WhereNode):
    def make_atom(self, child, qn):
        table_alias, name, db_type, lookup_type, value_annot, params = child

        if lookup_type in INET_TERMS:
            return ('%s.%s %s inet %%s' % (table_alias, name, INET_TERMS[lookup_type]), params)

        return super(IPWhere, self).make_atom(child, qn)

class IPManger(models.Manager):
    def get_query_set(self):
        q = IPQuery(self.model, connection, IPWhere)
        return query.QuerySet(self.model, q)

class IPAddressField(models.IPAddressField):
    __metaclass__ = models.SubfieldBase

    def db_type(self):
        return 'inet'

    def to_python(self, value):
        if not value:
            return None

        try:
            return IP(value)
        except ValueError, e:
            raise ValidationError(e)

    def get_db_prep_value(self, value):
        return unicode(self.to_python(value))

    def get_db_prep_lookup(self, lookup_type, value):
        value = unicode(value)

        if lookup_type in INET_TERMS:
            return [value]

        return super(IPAddressField, self).get_db_prep_lookup(lookup_type, value)

class Foo(models.Model):
    ip = IPAddressField()

    objects = IPManger()

    def __unicode__(self):
        return unicode(self.ip)