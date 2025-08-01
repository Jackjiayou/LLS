APPId = "094ce94e"
APIKey = "7c3c7ba03eb9b7209984050f258809c7"
APISecret = "NmY0YmYwMmVjYWI2NmIxNGExMzkxMDQw"
audio_path = ""

# 请求数据
request_data = {
	"header":{
		"app_id":"123456",
		"status":0
	},
	"parameter":{
		"st":{
			"lang":"cn",
			"core":"para",
			"refText":"",
			"result":{
				"encoding":"utf8",
				"compress":"raw",
				"format":"plain"
			}
			# "getParam":0,
			# "attachAudioUrl":0,
			# "vad":0,
			# "seek":0,
			# "ref_length":0,
			# "phoneme_output":0,
			# "slack":0,
			# "scale":0,
			# "precision":0,
			# "refPinyin":"",
			# "serverTimeout":0,
			# "output_rawtext":0,
			# "realtime_feedback":0,
			# "customized_lexicon":"",
			# "phoneme_diagnosis":0,
			# "dict_type":"",
			# "paragraph_need_word_score":0,
		}
	},
	"payload":{
		"data":{
			"encoding":"lame",
			"sample_rate":16000,
			"channels":1,
			"bit_depth":16,
			"status":0,
			"seq":0,
			"audio":audio_path,
			"frame_size":0
		}
	}
}

# 请求地址
request_url = "wss://cn-east-1.ws-api.xf-yun.com/v1/private/s8e098720"

# 用于快速定位响应值

response_path_list = ['$..payload.result', ]