extends Node

const CHARACTER_PATH := "res://data/角色.json"
const QUEST_PATH := "res://data/任務.csv"

func _ready() -> void:
	var character_data := _load_character()
	var quest_data := _load_quests()
	print("MVP Prototype Loaded")
	print("角色：", character_data)
	print("任務：", quest_data)

func _load_character() -> Dictionary:
	var file := FileAccess.open(CHARACTER_PATH, FileAccess.READ)
	if file == null:
		return {}
	var content := file.get_as_text()
	var result := JSON.parse_string(content)
	if typeof(result) != TYPE_DICTIONARY:
		return {}
	return result

func _load_quests() -> Array:
	var file := FileAccess.open(QUEST_PATH, FileAccess.READ)
	if file == null:
		return []
	var content := file.get_as_text()
	var lines := content.strip_edges().split("\n", false)
	if lines.size() <= 1:
		return []
	var headers := lines[0].split(",")
	var quests: Array = []
	for i in range(1, lines.size()):
		var row := lines[i].split(",")
		var item := {}
		for j in range(min(headers.size(), row.size())):
			item[headers[j]] = row[j]
		quests.append(item)
	return quests
