import requests
import json
import re

import dearpygui.dearpygui as dpg

dpg.create_context()
dpg.create_viewport(title='GoodCompany Debug Viewer', width=600, height=300)

def jsonCoordToDrawCoordWithOffset(jsonCoord, offset):
    return (1000 - jsonCoord["X"] * 10 + offset[0], 1000 + jsonCoord["Y"] * 10 + offset[1])

rotMat90CW = (
    (0, -1),
    (1, 0),
)

rotMat90CCW = (
    (0, 1),
    (-1, 0),
)

rotMat180 = (
    (-1, 0),
    (0, -1),
)

def jsonTransformedCoordToDrawCoord(jsonCoord, jsonTransform):
    localCoord = (-jsonCoord["X"] * 10, jsonCoord["Y"] * 10)
    if jsonTransform["Orientation"] == 1:
        localCoord = (
            rotMat90CW[0][0] * localCoord[0] + rotMat90CW[0][1] * localCoord[1],
            rotMat90CW[1][0] * localCoord[0] + rotMat90CW[1][1] * localCoord[1]
        )
    elif jsonTransform["Orientation"] == 2:
        localCoord = (
            rotMat180[0][0] * localCoord[0] + rotMat180[0][1] * localCoord[1],
            rotMat180[1][0] * localCoord[0] + rotMat180[1][1] * localCoord[1]
        )
    elif jsonTransform["Orientation"] == 3:
        localCoord = (
            rotMat90CCW[0][0] * localCoord[0] + rotMat90CCW[0][1] * localCoord[1],
            rotMat90CCW[1][0] * localCoord[0] + rotMat90CCW[1][1] * localCoord[1]
        )
    return jsonCoordToDrawCoordWithOffset(jsonTransform["Position"], localCoord)

class ChainData:
    def __init__(self, chainJson) -> None:
        chainID = chainJson["ChainID"]
        brokenStr = "(BROKEN)" if chainJson["PathSeemsBroken"] else ""
        self.chainLabel = f"Chain {chainID} {brokenStr}"
        self.chainID = chainID
        self.chainJson = chainJson

    def __str__(self) -> str:
        return self.chainLabel

class ChainList:
    def __init__(self):
        self.chainList = []

    def deInitialize(self):
        dpg.delete_item("chainRenderContainer", children_only=True)
        dpg.delete_item("chainlist", children_only=True)
        dpg.delete_item("chaindetail", children_only=True)

    def initialize(self, chainsJson) -> None:
        dpg.delete_item("chainRenderContainer", children_only=True)
        dpg.delete_item("chainlist", children_only=True)
        with dpg.drawlist(2000, 2000, tag="render", parent="chainRenderContainer"):
            with dpg.draw_layer(tag="colliders"):
                pass
            self.chainList = []
            for chain in chainsJson.values():
                if len(chain["ChainPath"]) == 0:
                    continue
                chainID = chain["ChainID"]
                self.chainList.append(ChainData(chain))
                with dpg.draw_layer(tag="chain%dback" % chainID):
                    lastCoord = chain["ChainPath"][0]
                    for coord in chain["ChainPath"]:
                        if lastCoord == coord:
                            continue
                        fromCoord = jsonCoordToDrawCoordWithOffset(lastCoord, (5,5))
                        toCoord = jsonCoordToDrawCoordWithOffset(coord, (5,5))
                        dpg.draw_arrow(toCoord, fromCoord, color=(150, 150, 150, 255), thickness=1)
                        lastCoord = coord
                with dpg.draw_layer(tag="chain%d" % chainID):
                    lastCoord = chain["ChainPath"][0]
                    for coord in chain["ChainPath"]:
                        if lastCoord == coord:
                            continue
                        fromCoord = jsonCoordToDrawCoordWithOffset(lastCoord, (5, 5))
                        toCoord = jsonCoordToDrawCoordWithOffset(coord, (5, 5))
                        dpg.draw_arrow(toCoord, fromCoord, color=(255, 255, 255, 255), thickness=2)
                        lastCoord = coord
                    dpg.configure_item("chain%d" % chainID, show=False)
        dpg.add_listbox(parent="chainlist", items=self.chainList, num_items=len(self.chainList), callback=self.chainSelected)

    def chainSelected(self, sender, selectedChain):
        dpg.delete_item("chaindetail", children_only=True)
        for chain in self.chainList:
            dpg.configure_item("chain%d" % chain.chainID, show=str(chain) == selectedChain)
            dpg.configure_item("chain%dback" % chain.chainID, show=str(chain) != selectedChain)
            if str(chain) == selectedChain:
                for element in chain.chainJson["ConveyorElements"]:
                    dpg.add_text(parent="chaindetail",
                                 default_value="%s (%d)" % (element["EntityType"], element["ElementID"]))
                    dpg.add_text(parent="chaindetail", indent=10,
                                 default_value=element["ChainElementType"])

chainlist = None
def loadAndShowConveyorChain():
    global chainlist
    dpg.configure_item("loadChainButton", enabled=False, label="loading...")
    r = requests.get("http://127.0.0.1:51274/debug/chains")
    if r.status_code != 200:
        print(f"ERROR: couldn't load chains debug url. Error: {r.status_code}")
        return
    chainsJson = json.loads(r.text)
    if chainlist != None:
        chainlist.deInitialize()
        chainlist = None
    chainlist = ChainList()
    chainlist.initialize(chainsJson)

    print(f"success: {r.status_code}")
    dpg.configure_item("loadChainButton", enabled=True, label="Refresh")

    r = requests.get("http://127.0.0.1:51274/debug")
    debugJson = json.loads(r.text)
    for entityComps in debugJson.values():
        if "TileColliderComponent" in entityComps:
            tileCollider = entityComps["TileColliderComponent"]
            tileTransform = entityComps["TileTransformComponent"]
            for localCoord in tileCollider["BlockedTilePositions"]:
                globalCoord = jsonTransformedCoordToDrawCoord(localCoord, tileTransform)
                dpg.draw_rectangle(globalCoord, (globalCoord[0]+10, globalCoord[1]+10), parent="colliders",
                                   color=(50, 50, 50, 255), fill=(50, 50, 50, 255))


with dpg.window(label="ConveyorChain Debugger", no_scrollbar=True):
    with dpg.group(tag="topBar", horizontal=True):
        dpg.add_button(tag="loadChainButton", label="Refresh", callback=loadAndShowConveyorChain)

    with dpg.group(horizontal=True):
        with dpg.child_window(tag="sidebar", width=300, no_scrollbar=True):
            with dpg.child_window(tag="chainlist", height=500):
                pass
            with dpg.child_window(tag="chaindetail", autosize_y=True, label="Chain Details"):
                pass
        with dpg.child_window(tag="chainRenderContainer", horizontal_scrollbar=True):
            pass

class EntityWindow:
    def __init__(self, entityStr):
        entityIDMatch = entityIDRegex.search(entityStr)
        self.entityID = int(entityIDMatch.groups()[0])
        self.windowID = dpg.add_window(label=entityStr)
        self.refresh()

    def refresh(self):
        dpg.delete_item(self.windowID, children_only=True)
        dpg.add_button(parent=self.windowID, label="refresh", callback=self.refresh)
        r = requests.get("http://127.0.0.1:51274/debug/%d" % self.entityID)
        debugJson = json.loads(r.text)
        for entityComps in debugJson.values():
            for compName, compValue in entityComps.items():
                with dpg.tree_node(parent=self.windowID, label=compName, default_open=False):
                    dpg.add_text(json.dumps(compValue, indent=2))

def openWindowForEntity(sender, entityStr):
    EntityWindow(entityStr)

entityIDRegex = re.compile(r"#(\d+)")
entityList = None
def loadAndShowEntities():
    global entityList
    r = requests.get("http://127.0.0.1:51274/debug/list")
    debugListJson = json.loads(r.text)
    entityList = []
    for entity in debugListJson["Entities"]:
        for entityName, entityID in entity.items():
            entityList.append("%s #%d" % (entityName, entityID))

    dpg.set_value("filterInput", "")
    dpg.delete_item("entityList", children_only=True)
    dpg.add_listbox(tag="entitiesListBox", parent="entityList", items=entityList, num_items=len(entityList),
                    callback=openWindowForEntity)

def filterEntityList(sender, filterString):
    filteredList = [e for e in entityList if filterString.lower() in e.lower()]
    dpg.configure_item("entitiesListBox", items=filteredList)

with dpg.window(label="Entity Debugger", no_scrollbar=True):
    with dpg.group(tag="entityTopBar", horizontal=True):
        dpg.add_button(tag="loadEntitiesButton", label="Refresh", callback=loadAndShowEntities)
        dpg.add_input_text(tag="filterInput", label="Filter", callback=filterEntityList)
    with dpg.child_window(tag="entityList", autosize_y=True, label="Entity List"):
        pass



dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
