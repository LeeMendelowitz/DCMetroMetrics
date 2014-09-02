class WebJSONMixin(object):

  def to_web_json(self):
    
    fields = getattr(self, 'web_json_fields', [])

    return dict((k, getattr(self, k, None)) for k in fields)