import sys

sys.path.append("/usr/src/app/api")

survey_template = {
	"type": "object",
	"properties": {
		"survey_id": {"type": "string"},
		"image": {"type": "string"},
		"name": {"enum": ["hotel rooms", "restaurants", "airlines", "grocery store", "car dealership", "default"]}
	},
	"required": ["survey_id", "image", "name"]
}

survey_answer = {
	"type": "object",
	"properties": {
		"viewid": {"type": "string"},
		"answer": {
			"type": "array",
			"items": {
				"type": "object",
				"properties": {
					"questionId": {"type": "number"},
					"value": {"type": ["number", "string", "boolean", "array"]},
					"comment": {"type": "string"},
					"otherComments": {"type": "string"}
				},
				"required": ["questionId", "value"]
			}
		},
		"duration": {"type": "number"},
		"channel": {
			"type": "object",
			"properties": {
				"type": {"enum": ["web", "qrcode"]},
				"template": {"type": "string"},
				"name": {"type": "string"}
			}
		},
		"version_name": {"type": "string"}
	},
	"required": ["viewid", "answer", "duration", "channel"]
}

survey_periodic_feedback = {
	"type": "object",
	"properties": {
		"viewid": {"type": "string"},
		"periode": {"enum": ["today", "last 7 days", "last 30 days", "all", "custom"]},
		"startDate": {"type": "string"},
		"endDate": {"type": "string"}
	},
	"required": ["viewid", "periode"]
}

contact = {
	"type": "object",
	"properties": {
		"viewid": {"type": "string"},
		"name": {"type": "string"},
		"phone": {"type": "string"}
	},
	"required": ["viewid", "name", "phone"]
}

edit_survey: dict = {
	"type": "object",
	"properties": {
		"parent": {"type": "string"},
		"version_name": {"type": "string"},
		"description": {"type": "string"},
		"questions": {
			"type": "array",
			"items": {
				"type": "object",
				"properties": {
					"questionId": {"type": "number"},
					"questionOrder": {"type": "number"},
					"questionType": {"type": "number"},
					"questionDetails": {"type": "object"},
					"answerDetails": {"type": "object"}
				}
			}
		},
		"settings": {"type": "object"}
	},
	"required": ["parent", "version_name", "description", "questions", "settings"]
}

welcome: dict = {
	"type": "object",
	"properties": {
		"option": {"enum": ["default", "custom"]},
		"heading_text": {"type": "string"},
		"message": {"type": "string"}
	},
	"required": ["option", "heading_text", "message"]
}

thank_you: dict = {
	"type": "object",
	"properties": {
		"image": {"type": "string"},
		"option": {"enum": ["default", "custom"]},
		"heading_text": {"type": "string"},
		"message": {"type": "string"}
	},
	"required": ["image", "option", "heading_text", "message"]
}

logo: dict = {
	"type": "object",
	"properties": {
		"link": {"type": "string"},
		"display_size_option": {"type": "string"},
		"position": {"type": "string"}
	},
	"required": ["link", "display_size_option", "position"]
}

welcome: dict = {
    "type": "object",
    "properties": {
        "option": {"enum": ["default", "custom"]},
        "heading_text": {"type": "string"},
        "message": {"type": "string"}
    },
    "required": ["option", "heading_text", "message"]
}

thank_you: dict = {
    "type": "object",
    "properties": {
        "image": {"type": "string"},
        "option": {"enum": ["default", "custom"]},
        "heading_text": {"type": "string"},
        "message": {"type": "string"}
    },
    "required": ["image", "option", "heading_text", "message"]
}

logo: dict = {
    "type": "object",
    "properties": {
        "link": {"type": "string"},
        "display_size_option": {"type": "string"},
        "position": {"type": "string"}
    },
    "required": ["link", "display_size_option", "position"]
}
