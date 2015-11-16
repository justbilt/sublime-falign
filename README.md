A alignment plugin for Sublime Text 2 and 3.

![][1]

# Installation

To install this plugin, you have two options:

1. If you have Package Control installed, simply search for `FAlign` to install.

2. Clone source code to Sublime Text packages folder.

# Usage

`⌘ + \` alignment with first keyword. Again alignment with second keyword,...

# Examples

Before:
```
Button = import(".utils.Button")
AlertEx = import(".utils.AlertEx")
Tips = import(".utils.Tips")
Help = import(".utils.Help")
```
After:
```
Button  = import(".utils.Button")
AlertEx = import(".utils.AlertEx")
Tips    = import(".utils.Tips")
Help    = import(".utils.Help")
```


Before:
```
dispatcher:addEventListener("mail_new", mail_new)
dispatcher:addEventListener("mail_mark_read", mail_mark_read)
dispatcher:addEventListener("mail_handle_invitation", mail_handle_invitation)
dispatcher:addEventListener("mail_send", mail_send)
```

After:
```
dispatcher:addEventListener("mail_new",               mail_new)
dispatcher:addEventListener("mail_mark_read",         mail_mark_read)
dispatcher:addEventListener("mail_handle_invitation", mail_handle_invitation)
dispatcher:addEventListener("mail_send",              mail_send)
```


Before:
```
local name = params.name or "Arial"
local font_size = params.font_size or 30
local color = params.color or cc.c3b(255, 255, 255)
local width = params.width or 0
```

After:
```
local name      = params.name      or "Arial"
local font_size = params.font_size or 30
local color     = params.color     or cc.c3b(255, 255, 255)
local width     = params.width     or 0
```



[1]: http://ww4.sinaimg.cn/large/7f870d23gw1exv5kflm7ug20ov0213yx.gif
