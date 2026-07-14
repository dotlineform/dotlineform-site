---
doc_id: visual-code
title: Visual Code
added_date: "2026-07-14 17:47"
last_updated: "2026-07-14 17:47"
parent_id: unsorted
---
# Visual Code


How to use Visual Code with Processing

run sketch:  <span style="background-color: #00C6BD;">
     Ctrl+Shift+B
 </span>

## VS Code Extension

Prep:

1. in Processing, install Tools > Install Processing-java: needs to be for all users
2. n extensions, search for Processing Language
3. install extension

How to use:
	
1. open .pde file
2. cmd-shift-p Create Task File - this adds a .vscode/tasks.json file to the sketch folder
3. cmd-shift-b runs the task file
4. which runs the code in processing and displays result in a new window

## ________________________________________________________
## 
## What this extension is
This is a Visual Studio Code extension created by Tobiah Zarlez to add Processing language support.

## What this extension isn't
This extension does not allow you to debug Java or Processing projects.

## Can you add a feature I want?
Possibly! [Let us know](https://github.com/TobiahZ/processing-vscode/issues), we'd love to hear your suggestions.

## Installation Instructions
1. Open [Visual Studio Code](https://code.visualstudio.com/)Open the Command Pallet (CTRL+SHIFT+P for Windows/Linux or CMD+SHIFT+P on Mac) enter the command “Install Extension”
4. Search for “Processing Language” and click on this extension.
5. Restart Visual Studio Code
## 
## Feature list
## 
## Syntax highlighting
Open any .pde file, or simply choose "Processing" from the drop down menu in the bottom right corner.
## 
## Snippets
Once the language has been set, you will see code snippets pop up automatically as you type!
## 
## Commands
Installing this extension will add the following commands to your command pallette (CTRL+SHIFT+P, or opened by View -> Command Pallette). These commands can be selected and run from there, to complete the corresponding tasks.
## 
## Command: Create Task File
Adds a .vscode/tasks.json file to your project folder, that has the contents of the ProcessingTasks.json located in the root folder of this project.
When you run this task (Keyboard shortcut: Ctrl+Shift+B), it will compile and run your project!
If you would like to see output from the compiler, simply comment out the line "showOutput": "never",

**NOTE:** Processing must be added to your path, or you must set the "processing.path" setting!
Follow [these instructions](vscode-webview://0socl50b5kl61totdfr6brsq2pp5qdhnl38t4k5qthjcfc9mgfke/index.html?id=dcd1585f-10f5-4cad-9be2-69acfc71d388&origin=165a708b-0133-4295-a9cd-7426045c8d1c&swVersion=4&extensionId=&platform=electron&vscode-resource-base-authority=vscode-resource.vscode-cdn.net&parentOrigin=vscode-file%3A%2F%2Fvscode-app&disableServiceWorker=true#add-processing-to-path) to add Processing to your path, or these [alternate instructions](vscode-webview://0socl50b5kl61totdfr6brsq2pp5qdhnl38t4k5qthjcfc9mgfke/index.html?id=dcd1585f-10f5-4cad-9be2-69acfc71d388&origin=165a708b-0133-4295-a9cd-7426045c8d1c&swVersion=4&extensionId=&platform=electron&vscode-resource-base-authority=vscode-resource.vscode-cdn.net&parentOrigin=vscode-file%3A%2F%2Fvscode-app&disableServiceWorker=true#alternate-method) instead to modify the path setting.
See "[Requirements](vscode-webview://0socl50b5kl61totdfr6brsq2pp5qdhnl38t4k5qthjcfc9mgfke/index.html?id=dcd1585f-10f5-4cad-9be2-69acfc71d388&origin=165a708b-0133-4295-a9cd-7426045c8d1c&swVersion=4&extensionId=&platform=electron&vscode-resource-base-authority=vscode-resource.vscode-cdn.net&parentOrigin=vscode-file%3A%2F%2Fvscode-app&disableServiceWorker=true#requirements)" for full details.
## 
## Command: Run Processing Project
This is just a shortcut for running the .vscode/tasks.json file. Same as pressing  <span style="background-color: #00C6BD;">
     Ctrl+Shift+B
 </span>

**Note: Must have ran the "Create Processing Task File" command first,** **[see above](vscode-webview://0socl50b5kl61totdfr6brsq2pp5qdhnl38t4k5qthjcfc9mgfke/index.html?id=dcd1585f-10f5-4cad-9be2-69acfc71d388&origin=165a708b-0133-4295-a9cd-7426045c8d1c&swVersion=4&extensionId=&platform=electron&vscode-resource-base-authority=vscode-resource.vscode-cdn.net&parentOrigin=vscode-file%3A%2F%2Fvscode-app&disableServiceWorker=true#command-create-task-file)****!**
## 
## Command: Open Extension Documentation
Opens this documentation.
By default uses processing.org's documentation. Can change to p5js's if preferred using the processing.docs setting.
## 
## Command: Open Documentation for Selection
Use the pallet command "Processing: Open Documentation for Selection" to open the processing documentation for the current selection.
By default uses processing.org's documentation. Can change to p5js's if preferred using the processing.docs setting.
## 
## Command: Search Processing Website
Use the pallet command "Processing: Search Processing Website" to quickly search whatever you want on the processing website.
By default uses processing.org's documentation. Can change to p5js's if preferred using the processing.docs setting.
By default uses Google for search. Can change to DuckDuckGo if preferred using the processing.search setting.
## 
## Requirements
Installing the extension will give you instant access to [syntax highlighting](vscode-webview://0socl50b5kl61totdfr6brsq2pp5qdhnl38t4k5qthjcfc9mgfke/index.html?id=dcd1585f-10f5-4cad-9be2-69acfc71d388&origin=165a708b-0133-4295-a9cd-7426045c8d1c&swVersion=4&extensionId=&platform=electron&vscode-resource-base-authority=vscode-resource.vscode-cdn.net&parentOrigin=vscode-file%3A%2F%2Fvscode-app&disableServiceWorker=true#syntax-highlighting) and [snippets](vscode-webview://0socl50b5kl61totdfr6brsq2pp5qdhnl38t4k5qthjcfc9mgfke/index.html?id=dcd1585f-10f5-4cad-9be2-69acfc71d388&origin=165a708b-0133-4295-a9cd-7426045c8d1c&swVersion=4&extensionId=&platform=electron&vscode-resource-base-authority=vscode-resource.vscode-cdn.net&parentOrigin=vscode-file%3A%2F%2Fvscode-app&disableServiceWorker=true#snippets).
However, in order to compile and run your processing project from Visual Studio Code, you will need to do three things:
1. Set up your .vscode/tasks.json file. (See: "[Command: Create Task File](vscode-webview://0socl50b5kl61totdfr6brsq2pp5qdhnl38t4k5qthjcfc9mgfke/index.html?id=dcd1585f-10f5-4cad-9be2-69acfc71d388&origin=165a708b-0133-4295-a9cd-7426045c8d1c&swVersion=4&extensionId=&platform=electron&vscode-resource-base-authority=vscode-resource.vscode-cdn.net&parentOrigin=vscode-file%3A%2F%2Fvscode-app&disableServiceWorker=true#command-create-task-file)")
4. Add Processing to your path **OR** Modify your .vscode/tasks.json file. (See: "[Add Processing to path](vscode-webview://0socl50b5kl61totdfr6brsq2pp5qdhnl38t4k5qthjcfc9mgfke/index.html?id=dcd1585f-10f5-4cad-9be2-69acfc71d388&origin=165a708b-0133-4295-a9cd-7426045c8d1c&swVersion=4&extensionId=&platform=electron&vscode-resource-base-authority=vscode-resource.vscode-cdn.net&parentOrigin=vscode-file%3A%2F%2Fvscode-app&disableServiceWorker=true#add-processing-to-path)" or "[alternate method](vscode-webview://0socl50b5kl61totdfr6brsq2pp5qdhnl38t4k5qthjcfc9mgfke/index.html?id=dcd1585f-10f5-4cad-9be2-69acfc71d388&origin=165a708b-0133-4295-a9cd-7426045c8d1c&swVersion=4&extensionId=&platform=electron&vscode-resource-base-authority=vscode-resource.vscode-cdn.net&parentOrigin=vscode-file%3A%2F%2Fvscode-app&disableServiceWorker=true#alternate-method)")
11. Have a <File>.pde whose filename matches the name of the project's folder (General Processing Requirement). Your file cannot contain any spaces or it will not run correctly.
## 
## Add Processing to path
In order to automatically compile and open from Visual Studio Code, I recommend adding Processing to your path.
## 
## What does that mean?
That means you should be able to type the processing from anywhere on your machine, and it will open Processing.
## 
## How do I do that?
It's easier than you might think!

**Windows**
* Open the "Advanced System Settings" by running sysdm.cpl
* In the "System Properties" window, click on the Advanced tab.
* In the "Advanced" section, click the Environment Variables button.
* Edit the "Path" variable. Append the processing path (Example: ;C:\Program Files\Processing-3.0.1\) to the variable value. Each entry is separated with a semicolon.

**Mac**
Open Processing, and click the Tools -> Install "processing-java" menu item.
**Note:** You will have to install processing-java for all users for this to work

**Linux**
Set your PATH to where your processing application is located.
Example: export PATH=$PATH:/opt/processing/processing-2.0b4
You also need to create an alias for processing-java in /bin/ instead of /usr/bin/.
Example: sudo ln -s /opt/processing/processing-java /bin/processing-java
## 
## Then what?
 <span style="background-color: #00C6BD;">
     Once you've installed Processing to your path, you just need to add the appropriate .vscode/tasks.json file to every Processing project.
 </span>
See the command "[Create Task File](vscode-webview://0socl50b5kl61totdfr6brsq2pp5qdhnl38t4k5qthjcfc9mgfke/index.html?id=dcd1585f-10f5-4cad-9be2-69acfc71d388&origin=165a708b-0133-4295-a9cd-7426045c8d1c&swVersion=4&extensionId=&platform=electron&vscode-resource-base-authority=vscode-resource.vscode-cdn.net&parentOrigin=vscode-file%3A%2F%2Fvscode-app&disableServiceWorker=true#command-create-task-file)"
## 
## Alternate Method

What if you cannot, or do not want to add Processing to your path?
Simply modify the processing.path setting to follow the path to wherever processing is installed on your machine. Be sure to remember to keep the processing-java at the end of the path!
To change settings in VSCode, here is a link to the [official documentation](https://code.visualstudio.com/docs/getstarted/settings).
(Remember, for Windows be sure to turn any "\" into "\\"!)

Example:
    "processing.path": "C:\\Program Files\\processing-3.0.1\\processing-java",
**NOTE:** This is untested on Mac and Linux
## 
## If needed: Overwrite default terminal

You may need to also overwrite your default terminal in order to get your task file to run correctly.
Following [the instructions on the official VSCode documentation](https://code.visualstudio.com/docs/editor/tasks#_common-questions), all you have to do is add a few extra lines to your task file once you generate it.

For example, if you are running Windows and want the task file to use Command Prompt ('cmd.exe') you can add an 'options' parameter under the 'windows' portion:
      "windows": {
        "options": {
            "shell": {
                "executable": "cmd.exe",
                "args": [
                    "/d", "/c"
                ]
            }
        },
        "args":  [
          "--force",
          {
            "value": "--sketch=${workspaceRoot}",
            "quoting": "strong"
          },
          {
            "value": "--output=${workspaceRoot}\\out",
            "quoting": "strong"
          },
          "--run"
        ]
      }
## 
## To Do List
* Take nice looking (Animated?) screen shots for README/Instructions
## 
## Credits
Syntax highlighting and snippets code based on the [Processing Sublime Text plugin](https://github.com/b-g/processing-sublime).
## 
## Other resources

Here are some other resources I recommend:
* [Processing's official site](https://processing.org/)[Tobiah Zarlez Blog](http://www.tobiahz.com/)
