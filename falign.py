import sublime
import sublime_plugin
import re




class FalignCommand(sublime_plugin.TextCommand):
	def get_indent_text(self, view, indent):
		if int(view.settings().get("translate_tabs_to_spaces", False)):
			return ' '*(int(view.settings().get("tab_size", 8))*indent)
		else:
			return '\t'*indent

	def get_indent_level(self, view, line_string):
		tab_size = int(view.settings().get("tab_size", 8))
		space_count = 0
		index = 0
		for c in line_string:
			if c == " ":
				space_count += 1
			elif c == "\t":
				space_count += tab_size
			else:
				line_string = line_string[index:]
				break
			index += 1
		return int(space_count/tab_size),line_string

	def keys_equal(self, keys1, keys2):
		if len(keys1) != len(keys2):
			return False

		for i in range(len(keys1)):
			if keys1[i][0] != keys2[i][0]:
				return False

		return True


	
	def get_line_key(self, view, line):
		key_list = []
		pos = 0
		pattern = re.compile(r"[{0}]".format("".join(self.align_words)))
		while True:
			match = pattern.search(line, pos)
			if not match : break
			pos = match.end()
			key_list.append([match.group(),pos])

		return key_list if len(key_list) > 0 else None


	def get_smiller_lines(self, view, main_row):
		main_indent_level, main_string = self.get_indent_level(view, self.get_line_text(view, main_row))

		pattern = re.compile(r"[^\w]")
		match = pattern.search(main_string)
		if not match: return False, None, None, None

		main_keys = self.get_line_key(view, main_string)
		if not main_keys: return False, None, None, None

		main_head = main_string[:match.end(0)]

		print("main_keys:",main_keys)
		row_region =[]
		row_string ={
			str(main_row):[main_string,main_keys]
		}
		for direction in [-1,1]:
			index = main_row + direction
			while True:
				indent, string = self.get_indent_level(view, self.get_line_text(view, index))
				if indent != main_indent_level : break
				match = pattern.search(string)
				if not match or string[:match.end(0)] != main_head: break
				keys = self.get_line_key(view, string)
				print(keys)
				if not keys or not self.keys_equal(main_keys, keys): break
				row_string[str(index)] = [string, keys]
				index += direction
			row_region.append(index+(-direction))

		return row_region[0]!=row_region[1], main_indent_level, row_region, row_string

	def get_line_text(self, view, index):
		return view.substr(view.line(view.text_point(index, 0)))

	def run(self, edit):
		view = self.view
		selection = view.sel()
		# get current row
		main_row = view.rowcol(view.lines(selection[0])[0].a)[0]
		
		self.align_words = [',','=',':']

		re,indent_level,row_region,row_string = self.get_smiller_lines(view, main_row)
		if not re: return
		
		print("111","111","111")
		print("1","1","1")

		keys_len = len(row_string[str(main_row)][1])
		for i in range(0,keys_len):
			pos_max = 0
			for key in row_string:
				pos_max = max(pos_max, row_string[key][1][i][1])

			for key in row_string:
				row_data = row_string[key]
				line = row_data[0]
				pos = row_data[1][i][1]
				dis = pos_max - pos
				if dis != 0:
					row_data[0] = line[:pos-1] + " "*(dis) + line[pos-1:]
					for ii in range(i, keys_len):
						row_string[key][1][ii][1] += dis

		string_list = [""]
		for row in range(row_region[0],row_region[1]):
			string_list.append(row_string[str(row)][0]+"\n")
		string_list.append(row_string[str(row_region[1])][0])
		
		view.replace(
			edit, 
			sublime.Region(view.text_point(row_region[0],0),view.text_point(row_region[1]+1,0)-1), 
			self.get_indent_text(view, indent_level).join(string_list)
		)

# This function removes the duplicates from a list and returns a new list without them
# It also preserves the order of the list
def ordered_remove_duplicates(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]


class ValignCommand(sublime_plugin.TextCommand):
	# Returns the line string for the given row.
	def get_line_string_for_row(self, row):
		view       = self.view
		text_point = view.text_point(row, 0)
		line       = view.line(text_point)
		return view.substr(line)

	# Calculates the indentation level of a row
	def get_indentation_for_row(self, row):
		line_string = self.get_line_string_for_row(row)

		# Skip empty lines
		if len(line_string.strip()) == 0: return None

		# Calculate indentation
		match              = re.search("^\s+", line_string)
		indentation_string = match.group(0) if match else None
		indentation        = len(indentation_string) if indentation_string else 0

		if self.use_spaces: indentation /= self.tab_size

		# A bit of a hacky fix for issue #7: in JavaScript, we'll treat "var " at the
		# beginning of a line as another level of indentation to allow alignment of common
		# JavaScript formatting conventions. In the future we'll extract this out into a
		# more general solution.
		if self.treat_var_as_indent and re.search("^\s*var ", line_string): indentation += 1

		return indentation

	# Expands the set of rows to all of the lines that match the current indentation level and are
	# not empty; except the stop_empty option is false
	def expand_rows_to_indentation(self, start_row):
		line_count, _     = self.view.rowcol(self.view.size())
		start_indentation = self.get_indentation_for_row(start_row)
		rows              = [ start_row ]

		# Expand upward and then downward from the selection.
		for direction in [-1, 1]:
			row = start_row + direction
			while row >= 0 and row < line_count + 1:
				# Calculate the current indentation level.
				row_indentation = self.get_indentation_for_row(row)

				# Stop at empty lines or skip them.
				if row_indentation is None:
					if self.stop_empty:
						break
					else:
						row += direction
						continue

				# Append or prepend rows and break when we hit inconsistent indentation.
				if row_indentation != start_indentation:
					break

				# Add row to the return value
				if direction is -1:
					rows.insert(0, row)
				else:
					rows.append(row)

				# Next row
				row += direction

		# Return the calculated rows
		return rows

	# Returns the character to align on based on the start row. Returns None if no proper character
	# is found.
	def calculate_alignment_character(self, row):
		line_string         = self.get_line_string_for_row(row)
		self.alignment_char = None

		for alignment_char in self.alignment_chars:
			if re.search("\\" + alignment_char["char"], line_string):
				self.alignment_char = alignment_char
				print("-->>", self.alignment_char)
				break

	# Adjusts the current alignment range based on the alignment character so that the range
	# contains only rows that contain the alignment character.
	def adjust_rows_for_alignment_character(self, rows, start_row):
		adjusted_rows  = []
		alignment_char = self.alignment_char
		start_i        = i = rows.index(start_row)

		# Check upward and then downward from the start row.
		for direction in [-1, 1]:
			while i >= 0 and i < len(rows):
				row         = rows[i]
				line_string = self.get_line_string_for_row(row)

				# Make sure the character exists on this line.
				if alignment_char == None:
					if not re.search("\S+\s+\S+", line_string): break
				else:
					if not re.search("\\" + alignment_char["char"], line_string): break

				# Add the row.
				if direction == -1:
					adjusted_rows.insert(0, row)
				else:
					adjusted_rows.append(row)

				# Move on to the next row.
				i += direction

			# Reset i.
			i = start_i + 1

		# Return the new adjusted rows.
		return adjusted_rows

	# Normalizes the rows, creating a consistent format for alignment.
	def normalize_rows(self, edit):
		view           = self.view
		alignment_char = self.alignment_char

		for row in self.rows:
			line_string     = self.get_line_string_for_row(row)
			replace_pattern = ""
			replace_string  = ""

			if alignment_char == None:
				replace_pattern = "(?<=\S)\s+"
				replace_string  = " "
			else:
				replace_pattern = "\s*\\" + alignment_char["char"] + "\s*"
				if alignment_char["left_space"]: replace_string += " "

				for prefix in alignment_char["prefixes"]:
					if re.search("\\" + prefix + "\\" + alignment_char["char"], line_string):
						replace_pattern = "\s*\\" + prefix + alignment_char["char"] + "\s*"
						replace_string += prefix
						break

				replace_string += alignment_char["char"]
				if alignment_char["right_space"]: replace_string += " "


			match       = re.search(replace_pattern, line_string)
			column_span = match.span()
			text_point  = view.text_point(row, 0)
			view.replace(edit, sublime.Region(text_point + column_span[0], text_point + column_span[1]), replace_string)

	# Aligns all the rows after they've been calculated.
	def align_rows(self, edit):
		view           = self.view
		rows           = self.rows
		alignment_char = self.alignment_char
		char_indexes   = []
		max_char_index = None

		# Gather all of the character indexes.
		for row in rows:
			line_string = self.get_line_string_for_row(row)
			index       = 0
			has_prefix  = False

			if alignment_char == None:
				index = re.search("\S\s", line_string).start() + 1
			else:
				index = re.search("\\" + alignment_char["char"], line_string).start()

				for prefix in alignment_char["prefixes"]:
					if line_string[index - 1] == prefix:
						index     -= 1
						has_prefix = True
						break

				if alignment_char["alignment"] == "left": index += 1

			char_index = { "index": index, "has_prefix": has_prefix }
			char_indexes.append(char_index)

			if not max_char_index or index > max_char_index["index"]: max_char_index = char_index

		# Do the alignment!
		for i in range(len(rows)):
			row                 = rows[i]
			char_index          = char_indexes[i]
			extra_spaces_needed = max_char_index["index"] - char_index["index"]
			line_string         = self.get_line_string_for_row(row)

			if char_index["has_prefix"]:
				if not max_char_index["has_prefix"]: extra_spaces_needed -= 1
			else:
				if max_char_index["has_prefix"]: extra_spaces_needed += 1

			view.insert(edit, view.text_point(row, 0) + char_index["index"], " " * extra_spaces_needed)

	# Runs the command.
	def run(self, edit):
		view      = self.view
		selection = self.selection = view.sel()
		settings  = self.settings  = view.settings()

		# Get the "main" row; the row with the main cursor
		main_row = view.rowcol(view.lines(selection[0])[0].a)[0]

		# Load the settings from the user file
		valign_settings = sublime.load_settings("VAlign.sublime-settings")

		# Get settings from the VAlign setting file
		self.align_words     = valign_settings.get("align_words", settings.get("va_align_words", True))
		self.alignment_chars = valign_settings.get("alignment_chars",
			settings.get("va_alignment_chars", [
				{
					"char":        ",",
					"alignment":   "right",
					"left_space":  False,
					"right_space": True,
					"prefixes":    [","]
				},
				{
					# PHP arrays
					"char":        "=>",
					"alignment":   "right",
					"left_space":  True,
					"right_space": True,
					"prefixes":    []
				},
				{
					"char":        "===",
					"alignment":   "right",
					"left_space":  True,
					"right_space": True,
					"prefixes":    []
				},
				{
					"char":        "=",
					"alignment":   "right",
					"left_space":  True,
					"right_space": True,
					"prefixes":    ["+", "-", "&", "|", "<", ">", "!", "~", "%", "/", "*", ".", "?", "="]
				},
				{
					"char":        ":",
					"alignment":   "left",
					"left_space":  False,
					"right_space": False,
					"prefixes":    []
				},
			])
		)
		
		self.stop_empty          = valign_settings.get("stop_empty", settings.get("va_stop_empty", True))
		self.tab_size            = int(settings.get("tab_size", 8))
		self.use_spaces          = settings.get("translate_tabs_to_spaces")
		self.treat_var_as_indent = settings.get("treat_var_as_indent", False)
		
		self.calculate_alignment_character(main_row)
		
		if self.alignment_char is None and not self.align_words: return
		
		self.rows = []
		
		for select in selection:
			# Store some useful stuff.
			lines     = view.lines(select)
			start_row = view.rowcol(lines[0].a)[0]
			
			# Bail if the start row is already in the rows array.
			if start_row in self.rows: continue
			
			# Bail if our start row is empty.
			if len(self.get_line_string_for_row(start_row).strip()) == 0: continue
			
			# Calculate the rows that are on the same indentation level
			calculated_rows = self.expand_rows_to_indentation(start_row)
			
			# Filter the rows if they contain the alignment character
			calculated_rows = self.adjust_rows_for_alignment_character(calculated_rows, start_row)
			
			# Add the filtered rows to the rows
			self.rows.extend(calculated_rows)
		
		# Bail that there are not duplicates in the rows
		self.rows = ordered_remove_duplicates(self.rows)

		# Bail if we have no rows
		if len(self.rows) == 0: return
		
		# Normalize the rows to get consistent formatting for alignment.
		self.normalize_rows(edit)
		
		# If we have valid rows, align them.
		if len(self.rows) > 0: self.align_rows(edit)
