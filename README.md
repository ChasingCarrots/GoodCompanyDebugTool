# Good Company Debug Tool
This is the internal python-based tool Chasing Carrots used to quickly visualize the state of a running Good Company game. We made it public in this state so that modders can also have a look at the data.
But we are also very open for anyone to add to this tool or clean up the code :) 

# Running
You will need Python3 with [DearPyGui](https://github.com/hoffstadt/DearPyGui) and [Requests](https://pypi.org/project/requests/) installed. 

When you start Good Company with the commandline argument `-enable_debug_server` and start a new game (or load a savegame) you can simply use the "Refresh" buttons in the debug tool to get the data. It will use the http server that Good Company internally started on localhost port 51274 (the server is only started when using that commandline argument!).

The most interesing window in the tool is the "Entity Debugger". It will get a list of all entities, which can be filtered. The individual entities can be clicked to open a window with all the current components and values for that entity.

![Entity Debugger](https://user-images.githubusercontent.com/2462958/178489153-e8129dbb-8dce-4a2f-b512-0a515c1550cf.png)

There is also a window to debug conveyor chains, which is very specific and probably not all that useful for most of you :) But it will also draw a map with all the colliders, which could be used as a basis for a new general map visualizer...

![Chain Debugger](https://user-images.githubusercontent.com/2462958/178489831-29f9ca76-f915-415f-8aa4-bd6a9cfe04d8.png)
