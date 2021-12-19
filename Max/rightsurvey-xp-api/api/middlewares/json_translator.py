import sys

sys.path.append("/usr/src/app/api")
import json
import falcon


class JSONTranslator(object):

    def process_request(self, req, resp):
        if req.content_length in (None, 0):
            return

        body = req.stream.read()

        try:
            if req.client_accepts_json and req.content_type == "application/json":
                req.context['doc'] = json.loads(body.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')
