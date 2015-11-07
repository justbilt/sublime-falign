import sublime
import sublime_plugin
import re

def Settings():
	return sublime.load_settings("FAlign.sublime-settings")

class FalignCommand(sublime_plugin.TextCommand):
	def get_indent_text(self, view, indent):
		if int(view.settings().get("translate_tabs_to_spaces", False)):
			return ' '*(int(self.tab_size)*indent)
		else:
			return '\t'*indent

	def get_line_feature(self, line_string):
		space_count = 0
		index = 0
		for c in line_string:
			if c == " ":
				space_count += 1
			elif c == "\t":
				space_count += self.tab_size
			else:
				line_string = line_string[index:]
				break
			index += 1

		# 缩进层级
		indent_level = int(space_count/self.tab_size)

		# 关键字列表
		key_list = []
		pos = 0
		while True:
			match = self.alignment_chars_pattern.search(line_string, pos)
			if not match : break
			pos = match.end()
			key_list.append({"key":match.group(),"pos":pos})

		return indent_level, key_list if len(key_list) > 0 else None, line_string

	def get_key_word(self, key):
		return (" " if self.fa_alignment_chars[key]["left_space"] else "") + key + (" " if self.fa_alignment_chars[key]["right_space"] else "")

	def get_line_text(self, view, index):
		return view.substr(view.line(view.text_point(index, 0)))

	def run(self, edit):
		view = self.view
		selection = view.sel()
		self.tab_size = int(view.settings().get("tab_size", 8))
		# 展开配置
		fa_alignment_chars = Settings().get("fa_alignment_chars",[])
		self.fa_alignment_chars = {}
		for v in fa_alignment_chars:
			for vv in v["prefixes"]:
				self.fa_alignment_chars[vv] = {
					"alignment": v["alignment"],
					"left_space": v["left_space"],
					"right_space": v["right_space"],
				}
		# 编译匹配正则
		words = []
		pattern = re.compile(r"\w")
		for v in self.fa_alignment_chars:
			if pattern.search(v):
				words.append('(?<=\W)'+v+'(?=\W)')
			else:
				words.append(v)
		self.alignment_chars_pattern = re.compile(r"({0})".format("|".join(words)))

		# 当前行的缩进,内容
		main_row = view.rowcol(view.lines(selection[0])[0].a)[0]
		main_indent_level, main_keys, main_string = self.get_line_feature(self.get_line_text(view, main_row))
		if not main_keys:
			return

		# 相似行的数据
		smiller_lines_data ={}
		for direction in [-1,1]:
			row_index = main_row + direction
			while True:
				indent, keys, string = self.get_line_feature(self.get_line_text(view, row_index))
				if indent != main_indent_level :
					break
				if not keys or keys[0]["key"] != main_keys[0]["key"]:
					break
				smiller_lines_data[row_index] = {"text":string, "keyword":keys}
				row_index += direction

		if not smiller_lines_data:
			return
		else:
			smiller_lines_data[main_row] = {"text":main_string, "keyword":main_keys}
		
		# 删除已经对齐的keyword
		while True:
			is_same_pos = True
			for row_id in smiller_lines_data:
				row_data = smiller_lines_data[row_id]
				if row_data:
					if row_data["keyword"][0]["key"] != main_keys[0]["key"]:
						smiller_lines_data[row_id] = False
					elif row_data["keyword"][0]["pos"] != main_keys[0]["pos"]:
						is_same_pos = False
			
			if is_same_pos:
				for row_id in smiller_lines_data:
					row_data = smiller_lines_data[row_id]
					if row_data:
						del row_data["keyword"][0]
						if len(row_data["keyword"]) <= 0:
							smiller_lines_data[row_id] = False

				if not smiller_lines_data[main_row]:
					return
			else:
				break

		# 重新整理这些行
		keyword = smiller_lines_data[main_row]["keyword"][0]["key"]
		align_keyword = self.get_key_word(keyword)
		row_region = []
		new_smiller_lines_data = {}
		for direction in [-1,1]:
			row_id = main_row + direction
			while True:
				if not row_id in smiller_lines_data:
					break
				row_data = smiller_lines_data[row_id]
				if row_data:
					new_smiller_lines_data[row_id] = {"text":row_data["text"], "pos":row_data["keyword"][0]["pos"]}
				else:
					break
				row_id += direction
			row_region.append(row_id+(-direction))

		if len(new_smiller_lines_data) <= 0:
			return
		else:
			new_smiller_lines_data[main_row] = {
				"text":smiller_lines_data[main_row]["text"], 
				"pos":smiller_lines_data[main_row]["keyword"][0]["pos"]
			}

		# 去除关键字周围的空白
		for row_id in new_smiller_lines_data:
			text = new_smiller_lines_data[row_id]["text"]
			pos = new_smiller_lines_data[row_id]["pos"]
			region = []
			for ids in [range(pos-len(keyword)-1,0,-1),range(pos,len(text))]:
				for i in ids:
					if text[i] != " ":
						region.append(i)
						break
			text = text[:region[0]+1]+align_keyword+text[region[1]:]
			pos = region[0] + len(align_keyword) +1

			new_smiller_lines_data[row_id] = {"text":text, "pos":pos}			


		# 对齐行
		pos_max = 0
		for row_index in new_smiller_lines_data:
			pos_max = max(pos_max, new_smiller_lines_data[row_index]["pos"])

		for row_index in new_smiller_lines_data:
			line = new_smiller_lines_data[row_index]["text"]
			pos = new_smiller_lines_data[row_index]["pos"]
			dis = pos_max - pos
			if dis != 0:
				if self.fa_alignment_chars[keyword]["alignment"] == "left":
					new_smiller_lines_data[row_index]["text"] = line[:pos] + " "*(dis) + line[pos:]
				else:
					new_smiller_lines_data[row_index]["text"] = line[:pos-len(align_keyword)] + " "*(dis) + line[pos-len(align_keyword):]
		
		# 拼接行
		aligned_lines = [""]
		for row in range(row_region[0],row_region[1]):
			aligned_lines.append(new_smiller_lines_data[row]["text"]+"\n")
		aligned_lines.append(new_smiller_lines_data[row_region[1]]["text"])

		# 替换文本
		view.replace(
			edit, 
			sublime.Region(view.text_point(row_region[0],0),view.text_point(row_region[1]+1,0)-1), 
			self.get_indent_text(view, main_indent_level).join(aligned_lines)
		)