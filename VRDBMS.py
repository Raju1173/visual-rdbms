import pygame
import math
import os
import csv
import pickle
import copy
import shutil

newPath = 'DATABASES'
if not os.path.exists(newPath):
    os.makedirs(newPath)

pygame.init()

os.environ['SDL_VIDEO_CENTERED'] = '1'
info = pygame.display.Info()

screenWidth, screenHeight = info.current_w, info.current_h

screen = pygame.display.set_mode((screenWidth - 10, screenHeight - 50), pygame.RESIZABLE)
pygame.display.set_caption("RDBMS")

clock = pygame.time.Clock()
running = True

def respValX(value, flooring=True):
    scaled = screen.get_width() * (value / 1920)
    return math.floor(scaled) if flooring else scaled

def respValY(value, flooring=True):
    scaled = screen.get_height() * (value / 1080)
    return math.floor(scaled) if flooring else scaled

zoomFactor = 1.0

class Database:
    def __init__(self, name, x, y, scale=True):
        self.name = name.upper()
        if scale:
            self.x = respValX(x)
            self.y = respValY(y)
        else:
            self.x = x
            self.y = y
        self.tables = []

    def draw(self):
        font = pygame.font.SysFont(mainFont, int(respValY(50, False) * zoomFactor), bold=True)
        text = font.render(self.name, True, (49,49,50))

        if selectedDatabase == self:
            pygame.draw.rect(screen, (0, 0, 0), (self.getRect()[0] + respValX(5, False) * zoomFactor, self.getRect()[1] + respValY(5, False) * zoomFactor, self.getRect()[2] + respValX(10, False) * zoomFactor, self.getRect()[3] + respValY(10, False) * zoomFactor), border_radius=int(respValX(10, False) * zoomFactor))
            pygame.draw.rect(screen, (203, 206, 210), (self.getRect()[0] - respValX(5, False) * zoomFactor, self.getRect()[1] - respValX(5, False) * zoomFactor, self.getRect()[2] + respValY(10, False) * zoomFactor, self.getRect()[3] + respValY(10, False) * zoomFactor), border_radius=int(respValX(10, False) * zoomFactor))
        else:
            pygame.draw.rect(screen, (203, 206, 210), self.getRect(), border_radius=int(respValX(10, False) * zoomFactor))

        textX = (self.x - cameraX) * zoomFactor + respValX(22, False) * zoomFactor
        textY = (self.y - cameraY) * zoomFactor + respValY(25, False) * zoomFactor / 2
        
        screen.blit(text, (textX, textY))
    
    def getRect(self):
        font = pygame.font.SysFont(mainFont, int(respValY(50, False) * zoomFactor), bold=True)
        text = font.render(self.name, True, "BLACK")

        drawX = (self.x - cameraX) * zoomFactor
        drawY = (self.y - cameraY) * zoomFactor
        rectWidth  = text.get_width() + respValX(20, False) * zoomFactor * 2
        rectHeight = text.get_height() + respValY(10, False) * zoomFactor * 2

        return pygame.Rect(drawX, drawY, rectWidth, rectHeight)

class Table:
    global zoomFactor

    minTableWidth = respValX(200, False)

    def __init__(self, name, columns, x, y, scale=True):
        self.name = name.upper()
        self.columns = [col.upper() for col in columns]
        self.types = ["I" for _ in columns]
        self.x = respValX(x) if scale else x
        self.y = respValY(y) if scale else y
        self.selectedColumnIndex = None
        self.primaryKeyIndex = None
        self.foreignKeys = []
        self.lastClickTime = 0

    def fitTextToWidth(self, font, text, maxWidth):
        ellipsis = "..."
        fullWidth = font.size(text)[0]

        if fullWidth <= maxWidth:
            return text

        ellipsisWidth = font.size(ellipsis)[0]
        trimmed = text
        while len(trimmed) > 0:
            trimmed = trimmed[:-1]
            if font.size(trimmed)[0] + ellipsisWidth <= maxWidth:
                return trimmed + ellipsis
        return ellipsis

    def draw(self):
        font = pygame.font.SysFont(mainFont, int(respValY(40, False) * zoomFactor), bold=True)
        colFont = pygame.font.SysFont(mainFont, int(respValY(28, False) * zoomFactor))

        textNameWidth, textNameHeight = font.size(self.name)
        colTextHeightScreen = colFont.get_height()
        colTextHeightWorld = colTextHeightScreen / zoomFactor + respValY(10, False)
        headerHeightWorld = textNameHeight / zoomFactor + respValY(15, False) * 2
        totalColumnsHeightWorld = len(self.columns) * colTextHeightWorld + (len(self.columns)-1) * respValY(3, False)
        totalTableHeightWorld = headerHeightWorld + totalColumnsHeightWorld + respValY(10, False) + respValY(50, False)

        paddingX = respValX(20, False)
        tableWidth = max(self.minTableWidth, (textNameWidth + paddingX*2)/zoomFactor)
        colInnerPadding = respValX(10, False)

        tableRect = pygame.Rect((self.x - cameraX)*zoomFactor, (self.y - cameraY)*zoomFactor, tableWidth*zoomFactor, totalTableHeightWorld*zoomFactor)

        if selectedTable == self:
            pygame.draw.rect(screen, (0, 0, 0), (tableRect.x+respValX(5,False)*zoomFactor, tableRect.y+respValY(5,False)*zoomFactor, tableRect.width+respValX(10,False)*zoomFactor, tableRect.height), border_radius=int(respValX(10,False)*zoomFactor))
            pygame.draw.rect(screen, (203, 206, 210), (tableRect.x-respValX(5,False)*zoomFactor, tableRect.y-respValX(5,False)*zoomFactor, tableRect.width+respValY(10,False)*zoomFactor, tableRect.height), border_radius=int(respValX(10,False)*zoomFactor))
        
        else:
            pygame.draw.rect(screen, (203, 206, 210), tableRect, border_radius=int(respValX(10,False)*zoomFactor))

        nameSurface = font.render(self.name, True, (49,49,50))
        nameX = tableRect.x + (tableRect.width - nameSurface.get_width())/2
        nameY = tableRect.y + respValY(15,False)/2*zoomFactor
        screen.blit(nameSurface, (nameX, nameY))

        for i, col in enumerate(self.columns):
            colYWorld = self.y + headerHeightWorld + i*colTextHeightWorld + i*respValY(3, False)
            colYScreen = (colYWorld - cameraY) * zoomFactor
            colXScreen = tableRect.x + (colInnerPadding + respValX(25, False))*zoomFactor
            colWidthScreen = tableWidth*zoomFactor - ((colInnerPadding + respValX(12.5, False))*2*zoomFactor)
            bgColor = (0, 0, 0) if self.selectedColumnIndex == i else (50, 50, 50)

            typeColor = (100, 50, 50)

            if self.types[i] == "I":
                typeColor = (100, 50, 50)
            elif self.types[i] == "F":
                typeColor = (50, 100, 50)
            elif self.types[i] == "S":
                typeColor = (50, 50, 100)
            else :
                typeColor = (100, 100, 50)

            pygame.draw.rect(screen, typeColor, (tableRect.x + (colInnerPadding - respValX(1.5, False))*zoomFactor, colYScreen, colWidthScreen - respValX(130, False)*zoomFactor, colTextHeightWorld*zoomFactor), border_radius=int(respValX(5, False)*zoomFactor))
            
            pygame.draw.rect(screen, bgColor, (colXScreen, colYScreen, colWidthScreen, colTextHeightWorld*zoomFactor), border_radius=int(respValX(5, False)*zoomFactor))

            safeColText = self.fitTextToWidth(colFont, col, colWidthScreen - respValX(20, False)*zoomFactor)
            colTextSurface = colFont.render(safeColText, True, (255,255,255))
            screen.blit(colTextSurface, (colXScreen + respValX(5, False)*zoomFactor, colYScreen + (colTextHeightWorld*zoomFactor - colTextSurface.get_height()) / 2))

            typeText = self.types[i]
            typeTextSurface = colFont.render(typeText, True, (200,200,200))
            screen.blit(typeTextSurface, (tableRect.x + (colInnerPadding)*zoomFactor + respValX(2.75, False)*zoomFactor, colYScreen + (colTextHeightWorld*zoomFactor - typeTextSurface.get_height()) / 2))
            
            if self.primaryKeyIndex == i:
                keyIconSize = colTextSurface.get_height()
                keyX = colXScreen + colWidthScreen - keyIconSize + respValX(7.5, False)*zoomFactor
                keyY = colYScreen + (colTextHeightWorld*zoomFactor - keyIconSize) / 2
                pygame.draw.circle(screen, (255, 223, 0), (keyX, keyY + keyIconSize * 0.2), keyIconSize * 0.3, 2)
                pygame.draw.line(screen, (255, 223, 0), (keyX, keyY + keyIconSize * 0.5), (keyX, keyY + keyIconSize), 2)
                pygame.draw.line(screen, (255, 223, 0), (keyX, keyY + keyIconSize * 0.8), (keyX - keyIconSize * 0.2, keyY + keyIconSize * 0.8), 2)

        plusButtonRect, minusButtonRect = self.getButtonsRects()
        pygame.draw.rect(screen, (50,50,50), plusButtonRect, border_radius=5)
        pygame.draw.rect(screen, (50,50,50), minusButtonRect, border_radius=5)
        pygame.draw.line(screen, "WHITE", (plusButtonRect.centerx - 5*zoomFactor, plusButtonRect.centery),
                         (plusButtonRect.centerx + 5*zoomFactor, plusButtonRect.centery), max(1,int(2*zoomFactor)))
        pygame.draw.line(screen, "WHITE", (plusButtonRect.centerx, plusButtonRect.centery - 5*zoomFactor),
                         (plusButtonRect.centerx, plusButtonRect.centery + 5*zoomFactor), max(1,int(2*zoomFactor)))
        pygame.draw.line(screen, "WHITE", (minusButtonRect.centerx - 5*zoomFactor, minusButtonRect.centery),
                         (minusButtonRect.centerx + 5*zoomFactor, minusButtonRect.centery), max(1,int(2*zoomFactor)))

    def getRect(self):
        font = pygame.font.SysFont(mainFont, int(respValY(40, False) * zoomFactor), bold=True)
        colFont = pygame.font.SysFont(mainFont, int(respValY(28, False) * zoomFactor))
        textNameWidth, textNameHeight = font.size(self.name)
        colTextHeightWorld = colFont.get_height()/zoomFactor + respValY(10, False)
        headerHeightWorld = textNameHeight / zoomFactor + respValY(15, False) * 2
        totalColumnsHeightWorld = len(self.columns) * colTextHeightWorld + (len(self.columns)-1) * respValY(3, False)
        totalTableHeightWorld = headerHeightWorld + totalColumnsHeightWorld + respValY(10, False) + respValY(50, False)
        tableWidth = max(self.minTableWidth, (textNameWidth + respValX(20,False)*2)/zoomFactor)
        return pygame.Rect((self.x-cameraX)*zoomFactor, (self.y-cameraY)*zoomFactor, tableWidth*zoomFactor, totalTableHeightWorld*zoomFactor)
    
    def getColumnRect(self, index):
        fontName = pygame.font.SysFont(mainFont, int(respValY(40, False) * zoomFactor), bold=True)
        textNameWidth, textNameHeight = fontName.size(self.name)
        colFont = pygame.font.SysFont(mainFont, int(respValY(28, False) * zoomFactor))
        colTextHeightWorld = colFont.get_height()/zoomFactor + respValY(10, False)
        headerHeightWorld = textNameHeight / zoomFactor + respValY(15, False)*2
        colYWorld = self.y + headerHeightWorld + index*colTextHeightWorld + index*respValY(3, False)
        colYScreen = (colYWorld - cameraY) * zoomFactor

        tableWidth = max(self.minTableWidth, textNameWidth + respValX(20,False)*2)
        colInnerPadding = respValX(10, False)
        colXScreen = (self.x - cameraX + colInnerPadding + respValX(25, False)) * zoomFactor
        colWidthScreen = (tableWidth - (colInnerPadding + respValX(12.5, False))*2) * zoomFactor

        return pygame.Rect(colXScreen, colYScreen, colWidthScreen, colTextHeightWorld*zoomFactor)
    
    def getTypeButtonRect(self, index):
        colRect = self.getColumnRect(index)
        typeButtonSize = colRect.height * 0.8
        typeButtonX = colRect.x - respValX(22.5, False)*zoomFactor
        typeButtonY = colRect.y + (colRect.height - typeButtonSize) / 2
        return pygame.Rect(typeButtonX, typeButtonY, typeButtonSize, typeButtonSize)

    def getHeaderRect(self):
        font = pygame.font.SysFont(mainFont, int(respValY(40, False) * zoomFactor), bold=True)
        text = font.render(self.name, True, (49,49,50))
        headerHeight = text.get_height()/zoomFactor + respValY(15,False)*2
        return pygame.Rect((self.x-cameraX)*zoomFactor, (self.y-cameraY)*zoomFactor, text.get_width()+respValX(20,False)*zoomFactor*2, headerHeight*zoomFactor)

    def getButtonsRects(self):
        fullTableRect = self.getRect()
        buttonSize = respValX(40,False)*zoomFactor
        padding = respValX(5,False)*zoomFactor
        minusX = int(fullTableRect.right - buttonSize - padding)
        minusY = int(fullTableRect.bottom - buttonSize - padding)
        minusButtonRect = pygame.Rect(minusX, minusY, buttonSize, buttonSize)
        plusX = int(minusX - buttonSize - padding)
        plusY = int(minusY)
        plusButtonRect = pygame.Rect(plusX, plusY, buttonSize, buttonSize)
        return plusButtonRect, minusButtonRect
    
    def addForeignKey(self, columnIndex, referencedTable, referencedColumnIndex):
        self.foreignKeys.append({
            "column": columnIndex,
            "ref_table": referencedTable,
            "ref_column": referencedColumnIndex
        })

selectedDatabase = None
openedDatabase = None
selectedTable = None
openedTable = None

undoStack = []
redoStack = []

def addToUndoStack():
    global redoStack, openedDatabase, openedTable, state, Databases
    redoStack = []
    
    fileSystemState = {}
    for root, dirs, files in os.walk('DATABASES'):
        for name in dirs:
            path = os.path.join(root, name)
            fileSystemState[path] = None
        for name in files:
            path = os.path.join(root, name)
            try:
                with open(path, 'r', newline='', encoding='utf-8') as f:
                    fileSystemState[path] = f.read()
            except IOError: continue

    currentState = {
        'Databases': copy.deepcopy(Databases),
        'openedDatabase_name': openedDatabase.name if openedDatabase else None,
        'openedTable_name': openedTable.name if openedTable else None,
        'state': state,
        'file_system': fileSystemState
    }

    undoStack.append(currentState)

def undo():
    global Databases, openedDatabase, openedTable, state, redoStack
    if len(undoStack) > 1:
        currentFileSystemState = {}
        for root, dirs, files in os.walk('DATABASES'):
            for name in dirs:
                path = os.path.join(root, name)
                currentFileSystemState[path] = None
            for name in files:
                path = os.path.join(root, name)
                try:
                    with open(path, 'r', newline='', encoding='utf-8') as f:
                        currentFileSystemState[path] = f.read()
                except IOError:
                    continue

        currentState = {
            'Databases': copy.deepcopy(Databases),
            'openedDatabase_name': openedDatabase.name if openedDatabase else None,
            'openedTable_name': openedTable.name if openedTable else None,
            'state': state,
            'file_system': currentFileSystemState
        }
        redoStack.append(currentState)

        lastState = undoStack.pop()

        Databases = lastState['Databases']
        state = lastState['state']

        if lastState['openedDatabase_name']:
            openedDatabase = next((db for db in Databases if db.name == lastState['openedDatabase_name']), None)

            if lastState['openedTable_name'] and openedDatabase:
                openedTable = next((t for t in openedDatabase.tables if t.name == lastState['openedTable_name']), None)

            else:
                openedTable = None

        else:
            openedDatabase = None

        restoreFileSystem(lastState['file_system'])

def redo():
    global Databases, openedDatabase, state, undoStack, openedTable
    if redoStack:
        currentFileSystemState = {}
        for root, dirs, files in os.walk('DATABASES'):
            for name in dirs:
                path = os.path.join(root, name)
                currentFileSystemState[path] = None
            for name in files:
                path = os.path.join(root, name)
                try:
                    with open(path, 'r', newline='', encoding='utf-8') as f:
                        currentFileSystemState[path] = f.read()
                except IOError: continue

        currentState = {
            'Databases': copy.deepcopy(Databases),
            'openedDatabase_name': openedDatabase.name if openedDatabase else None,
            'openedTable_name': openedTable.name if openedTable else None,
            'state': state,
            'file_system': currentFileSystemState
        }
        undoStack.append(currentState)

        nextState = redoStack.pop()
        
        Databases = nextState['Databases']
        state = nextState['state']
        if nextState['openedDatabase_name']:
            openedDatabase = next((db for db in Databases if db.name == nextState['openedDatabase_name']), None)

            if nextState['openedTable_name'] and openedDatabase:
                openedTable = next((t for t in openedDatabase.tables if t.name == nextState['openedTable_name']), None)
            else:
                openedTable = None
        else:
            openedDatabase = None

        fileSystemToRestore = nextState['file_system']
        restoreFileSystem(fileSystemToRestore)

def restoreFileSystem(targetFileState):
    current_paths = set()
    for root, dirs, files in os.walk('DATABASES', topdown=False):
        for name in files:
            current_paths.add(os.path.join(root, name))
        for name in dirs:
            current_paths.add(os.path.join(root, name))

    for path in current_paths:
        if path not in targetFileState:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path) and not os.listdir(path):
                    os.rmdir(path)
            except OSError:
                pass
    
    for path, content in targetFileState.items():
        if content is None:
            os.makedirs(path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', newline='', encoding='utf-8') as f:
                f.write(content)

def zoomIn():
    global gridSpacing
    global zoomFactor

    if gridSpacing < 160:
        gridSpacing += 1

        zoomFactor = gridSpacing / 15

def zoomOut():
    global gridSpacing
    global zoomFactor

    if gridSpacing > 10:
        gridSpacing -= 1

        zoomFactor = gridSpacing / 15

gradient = None

def createVignette(intensity=180, radiusFactor=1.5):
    width, height = screen.get_size()

    center = (width / 2, height / 2)

    vignette = pygame.Surface((width, height), pygame.SRCALPHA)

    maxDistance = math.hypot(center[0], center[1]) * radiusFactor

    for y in range(height):
        for x in range(width):
            dist = math.hypot(x - center[0], y - center[1])
            t = dist / maxDistance

            if t > 1:
                t = 1

            alpha = int(t * intensity)

            vignette.set_at((x, y), (*(0, 0, 0), alpha))

    global gradient

    gradient = pygame.Surface((width, height), pygame.SRCALPHA)

    for y in range(height):
        for x in range(width):
            dist = math.hypot(0, y)
            t = dist / math.hypot(0, center[1]) * 0.35

            if t > 1:
                t = 1

            alpha = int(t * 255)

            gradient.set_at((x, y), (*(0, 0, 0), alpha))

    return vignette

def drawBezier(c1, c2, cp):
    points = [c1]

    step = 1/30

    for i in range(30) :
        t = i * step
        x = (1 - t)**2 * c1[0] + 2 * (1 - t) * t * cp[0] + t**2 * c2[0]
        y = (1 - t)**2 * c1[1] + 2 * (1 - t) * t * cp[1] + t**2 * c2[1]
        points.append((x,y))

    points.append(c2)

    pygame.draw.lines(screen, "WHITE", False, points, 5)

gridSpacing = 15

cameraX, cameraY = -screen.get_width() / 2, -screen.get_height() / 2

Databases = []

dbNames = sorted([d for d in os.listdir('DATABASES') if os.path.isdir(os.path.join('DATABASES', d))])

if os.path.exists("save.txt"):
    try :
        f = open('save.txt', 'rb')

        Databases = pickle.load(f)

        f.close()

    except :
        pass

else:
    for i, name in enumerate(dbNames):
        Databases.append(Database(name.upper(), -200 - i*150, -200 - i*100))

    for db in Databases:
        for i in os.listdir(os.path.join('DATABASES', db.name)):
            if i.endswith('.csv'):
                tableName = i[:-4]
                columns = []
                with open(os.path.join('DATABASES', db.name, i), 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    try:
                        columns = next(reader)
                    except StopIteration:
                        columns = []
                db.tables.append(Table(tableName, columns, db.x + 50, db.y + 100 + len(db.tables) * 100, scale=False))

center = (screen.get_width()/2, screen.get_height()/2)

prevMX, prevMY = 0, 0
prevCX, prevCY = 0, 0

dragOffsetX = 0
dragOffsetY = 0

ty = center[1] + respValY(460)
fy = center[1] + respValY(750)

dragging = 1

oldName = ''

vignette = createVignette(intensity=255, radiusFactor=2)

cursor = '~'

mousedown = False

queryMode = False

query = [cursor]

start = pygame.time.get_ticks()

lastClickTime = 0
doubleClickThreshold = 400

draggingColumn = None

lastClickedTable = None
lastClickedCol = None

mainFont = 'Consolas'

state = 0

def queryExecutor(Query):
    global state
    global selectedDatabase, openedDatabase
    global query


    print(f"Executing query: {Query}")
    if Query.startswith("CREATE"):
        addToUndoStack()

        parts = Query.partition(" ")

        if state == 0:
            dbNames = [db.strip() for db in parts[2].split(',') if db.strip()]

            for dbName in dbNames:
                newDBName = dbName
                count = 1

                while os.path.exists(os.path.join('DATABASES', newDBName)):
                    newDBName = f"{dbName}_{count}"
                    count += 1

                newDB = Database(
                    newDBName,
                    cameraX + (screen.get_width() / 2) / zoomFactor,
                    cameraY + (screen.get_height() / 2) / zoomFactor,
                    scale=False
                )

                Databases.append(newDB)
                os.makedirs(os.path.join('DATABASES', newDBName))

        elif state == 1:
            tableName = parts[2].strip()
            newTableName = tableName
            count = 1

            existingTableNames = [table.name for table in openedDatabase.tables]

            while newTableName in existingTableNames:
                newTableName = f"{tableName}_{count}"
                count += 1

            newTable = Table(
                newTableName,
                [],
                cameraX + (screen.get_width() / 2) / zoomFactor,
                cameraY + (screen.get_height() / 2) / zoomFactor,
                scale=False
            )

            openedDatabase.tables.append(newTable)
            open(os.path.join('DATABASES', openedDatabase.name, f"{newTableName}.csv"), 'w').close()

    elif Query.startswith("DELETE FIELDS"):
        addToUndoStack()
        if state == 1 and openedDatabase is not None:
            try:
                rest = Query[len("DELETE FIELDS"):].strip()
                
                parts = rest.upper().split(" FROM ")
                
                fieldsPart, tableName = parts
                tableName = tableName.strip()
                fieldsToDelete = [f.strip() for f in fieldsPart.split(",") if f.strip()]
                
                targetTable = next((t for t in openedDatabase.tables if t.name.upper() == tableName), None)

                indicesToDelete = []

                for field in fieldsToDelete:
                    indicesToDelete.append(targetTable.columns.index(field))
                
                filePath = os.path.join('DATABASES', openedDatabase.name, f"{targetTable.name}.csv")

                with open(filePath, 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    all_data = [row for row in reader]

                new_data = [[item for i, item in enumerate(row) if i not in indicesToDelete] for row in all_data]

                with open(filePath, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(new_data)

                targetTable.columns = new_data[0] if new_data else []
                targetTable.types = [t for i, t in enumerate(targetTable.types) if i not in indicesToDelete]
                
            except :
                query = [*"ERROR DELETING FIELDS", cursor]
                return
            
    elif Query.startswith("RENAME FIELD"):
        addToUndoStack()
        if state == 1 and openedDatabase is not None:
            try:
                rest = Query[len("RENAME FIELD "):].strip()

                parts = rest.split(" TO ")

                oldName = parts[0].strip()
                newName = parts[1].split(" IN ")[0].strip()

                tableName = parts[1].split(" IN ")[1].strip()

                print(tableName, oldName, newName)

                targetTable = next((t for t in openedDatabase.tables if t.name.upper() == tableName), None)

                filePath = os.path.join('DATABASES', openedDatabase.name, f"{targetTable.name}.csv")

                with open(filePath, 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    all_data = [row for row in reader]

                header = all_data[0]
                header = [newName if col == oldName else col for col in header]
                new_data = [header] + all_data[1:]

                with open(filePath, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(new_data)

                targetTable.columns = new_data[0] if new_data else []

            except :
                query = [*"ERROR RENAMING FIELD", cursor]
                return

    elif Query.startswith("MOVE FIELD"):
        addToUndoStack()

        if state == 1 and openedDatabase is not None:
            try:
                rest = Query[len("MOVE FIELD "):].strip()

                tablePart, destCol = rest.split(") TO")
                tableName, srcCol = tablePart.split("(")
                
                tableName = tableName.strip().upper()
                srcCol = srcCol.strip().upper()
                destCol = destCol.strip().upper()

                table = next((t for t in openedDatabase.tables if t.name == tableName), None)
                if not table:
                    query = [*"TABLE NOT FOUND", cursor]
                    return
                if srcCol not in table.columns or destCol not in table.columns:
                    query = [*"COLUMN NOT FOUND", cursor]
                    return

                srcIndex = table.columns.index(srcCol)
                destIndex = table.columns.index(destCol)

                filePath = os.path.join('DATABASES', openedDatabase.name, f"{table.name}.csv")

                with open(filePath, 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    all_data = [row for row in reader]

                if not all_data:
                    return
                def move_index(row):
                    value = row.pop(srcIndex)
                    row.insert(destIndex, value)
                    return row

                new_data = [move_index(row.copy()) for row in all_data]

                with open(filePath, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(new_data)

                table.columns = new_data[0]

                if table.primaryKeyIndex is not None:
                    pk = table.primaryKeyIndex

                    if pk == srcIndex:
                        table.primaryKeyIndex = destIndex
                    else:
                        if srcIndex < pk <= destIndex:
                            table.primaryKeyIndex -= 1
                        elif destIndex <= pk < srcIndex:
                            table.primaryKeyIndex += 1


                for fk in table.foreignKeys:
                    columnIndex = fk["column"]

                    if columnIndex == srcIndex:
                        fk["column"] = destIndex
                    else:
                        if srcIndex < columnIndex <= destIndex:
                            fk["column"] -= 1
                        elif destIndex <= columnIndex < srcIndex:
                            fk["column"] += 1

                for other in openedDatabase.tables:
                    for fk in other.foreignKeys: 
                        if fk["ref_table"] == table:
                            refColumnIndex = fk["ref_column"]

                            if refColumnIndex == srcIndex:
                                fk["ref_column"] = destIndex
                            else:
                                if srcIndex < refColumnIndex <= destIndex:
                                    fk["ref_column"] -= 1
                                elif destIndex <= refColumnIndex < srcIndex:
                                    fk["ref_column"] += 1

            except Exception as e:
                print("MOVE FIELD ERROR:", e)
                query = [*"ERROR MOVING FIELD", cursor]
                return
            
    elif Query.startswith("ADD DATA"):
        addToUndoStack()

        if state == 2 and openedTable is not None:
            try:
                rest = Query[len("ADD DATA"):].strip()

                if not (rest.startswith("(") and rest.endswith(")")):
                    query = [*"ERROR: Invalid syntax. Use ADD DATA(v1, v2, ...)", cursor]
                    return

                inner = rest[1:-1].strip()

                rawValues = [v.strip() for v in inner.split(",")]

                if len(rawValues) != len(openedTable.columns):
                    query = [*f"ERROR: Expected {len(openedTable.columns)} values, got {len(rawValues)}", cursor]
                    return

                filePath = os.path.join("DATABASES", openedDatabase.name, f"{openedTable.name}.csv")
                with open(filePath, "r", newline="") as csvfile:
                    reader = csv.reader(csvfile)
                    all_data = [row for row in reader]

                header = all_data[0]
                rows = all_data[1:]

                for i in range(len(rows)):
                    if len(rows[i]) < len(header):
                        rows[i] += [""] * (len(header) - len(rows[i]))

                finalValues = []

                for i, value in enumerate(rawValues):
                    colType = openedTable.types[i]
                    colName = openedTable.columns[i]

                    if value.upper() == "NONE":
                        if openedTable.primaryKeyIndex == i:
                            query = [*f"ERROR: Primary key '{colName}' cannot be None", cursor]
                            return
                        finalValues.append("")
                        continue

                    if colType == "I":
                        if not value.lstrip("-").isdigit():
                            query = [*f"ERROR: Column '{colName}' expects INTEGER", cursor]
                            return
                        finalValues.append(value)

                    elif colType == "F":
                        try:
                            float(value)
                        except:
                            query = [*f"ERROR: Column '{colName}' expects FLOAT", cursor]
                            return
                        finalValues.append(value)

                    elif colType == "S":
                        finalValues.append(value)

                    elif colType == "B":
                        if value.lower() not in ("true", "false", "0", "1"):
                            query = [*f"ERROR: Column '{colName}' expects BOOLEAN (true/false)", cursor]
                            return
                        finalValues.append(value.lower())

                    else:
                        finalValues.append(value)

                if openedTable.primaryKeyIndex is not None:
                    pkIndex = openedTable.primaryKeyIndex
                    pkValue = finalValues[pkIndex]

                    for row in rows:
                        if row[pkIndex] == pkValue:
                            query = [*f"ERROR: Duplicate primary key '{pkValue}' in column '{header[pkIndex]}'", cursor]
                            return

                for fk in openedTable.foreignKeys:
                    colIndex = fk["column"]
                    refTable = fk["ref_table"]
                    refColIndex = fk["ref_column"]

                    val = finalValues[colIndex]

                    if val == "":
                        continue

                    refPath = os.path.join("DATABASES", openedDatabase.name, f"{refTable.name}.csv")
                    with open(refPath, "r", newline="") as csvfile:
                        reader = csv.reader(csvfile)
                        refData = [row for row in reader]

                    refHeader = refData[0]
                    refRows = refData[1:]

                    for i in range(len(refRows)):
                        if len(refRows[i]) < len(refHeader):
                            refRows[i] += [""] * (len(refHeader) - len(refRows[i]))

                    exists = False
                    for r in refRows:
                        if r[refColIndex] == val:
                            exists = True
                            break

                    if not exists:
                        query = [*f"ERROR: Foreign key '{val}' does not exist in table '{refTable.name}' column '{refHeader[refColIndex]}'", cursor]
                        return

                rows.append(finalValues)

                with open(filePath, "w", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(header)
                    writer.writerows(rows)

                query = [*f"1 ROW ADDED", cursor]
                return

            except Exception as e:
                query = [*f"ERROR IN ADD DATA: {e}", cursor]
                return
            
    elif Query.startswith("SET"):
        addToUndoStack()

        if state == 2 and openedTable is not None:
            try:
                rest = Query[len("SET"):].strip()

                if " WHERE " in rest:
                    setPart, wherePart = rest.split(" WHERE ", 1)
                else:
                    setPart = rest
                    wherePart = None

                if "=" not in setPart:
                    query = [*"ERROR: SET syntax must be SET column = value", cursor]
                    return

                setCol, setVal = setPart.split("=", 1)
                setCol = setCol.strip().upper()
                setVal = setVal.strip()

                filePath = os.path.join("DATABASES", openedDatabase.name, f"{openedTable.name}.csv")

                with open(filePath, "r", newline="") as csvfile:
                    reader = csv.reader(csvfile)
                    all_data = [row for row in reader]

                header = all_data[0]
                rows = all_data[1:]

                for i in range(len(rows)):
                    if len(rows[i]) < len(header):
                        rows[i] += [""] * (len(header) - len(rows[i]))

                if setCol not in header:
                    query = [*f"ERROR: Column {setCol} does not exist", cursor]
                    return

                setIndex = header.index(setCol)

                def row_matches(row, wherePart):
                    if wherePart is None:
                        return True

                    or_segments = [seg.strip() for seg in wherePart.split(" OR ")]

                    for or_part in or_segments:
                        and_parts = [a.strip() for a in or_part.split(" AND ")]
                        all_and_ok = True

                        for cond in and_parts:
                            if ">=" in cond:
                                col, val = cond.split(">="); op = ">="
                            elif "<=" in cond:
                                col, val = cond.split("<="); op = "<="
                            elif "!=" in cond:
                                col, val = cond.split("!="); op = "!="
                            elif ">" in cond:
                                col, val = cond.split(">"); op = ">"
                            elif "<" in cond:
                                col, val = cond.split("<"); op = "<"
                            elif " LIKE " in cond:
                                col, val = cond.split(" LIKE "); op = "LIKE"; val = val.strip("'").strip('"')
                            else:
                                col, val = cond.split("="); op = "="

                            col = col.strip().upper()
                            val = val.strip()

                            if col not in header:
                                all_and_ok = False
                                break

                            idx = header.index(col)
                            cell = row[idx]

                            if op == "LIKE":
                                if val.lower() not in cell.lower():
                                    all_and_ok = False
                                continue

                            try:
                                left = float(cell)
                                right = float(val)
                            except:
                                left = cell
                                right = val

                            if op == "="  and not (left == right): all_and_ok = False
                            if op == "!=" and not (left != right): all_and_ok = False
                            if op == ">"  and not (left >  right): all_and_ok = False
                            if op == "<"  and not (left <  right): all_and_ok = False
                            if op == ">=" and not (left >= right): all_and_ok = False
                            if op == "<=" and not (left <= right): all_and_ok = False

                        if all_and_ok:
                            return True

                    return False

                changed = 0
                for row in rows:
                    if row_matches(row, wherePart):
                        row[setIndex] = setVal
                        changed += 1

                with open(filePath, "w", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(header)
                    writer.writerows(rows)

                query = [*f"{changed} ROWS UPDATED", cursor]
                return

            except Exception as e:
                query = [*f"ERROR IN SET: {e}", cursor]
                return
            
    elif Query.startswith("DELETE ROWS"):
        addToUndoStack()

        if state == 2 and openedTable is not None:
            try:
                if " WHERE " not in Query:
                    query = [*"ERROR: DELETE ROWS requires WHERE", cursor]
                    return

                wherePart = Query.split(" WHERE ", 1)[1].strip()

                filePath = os.path.join("DATABASES", openedDatabase.name, f"{openedTable.name}.csv")
                with open(filePath, "r", newline="") as csvfile:
                    reader = csv.reader(csvfile)
                    all_data = [row for row in reader]

                header = all_data[0]
                rows = all_data[1:]

                for i in range(len(rows)):
                    if len(rows[i]) < len(header):
                        rows[i] += [""] * (len(header) - len(rows[i]))

                def row_matches(row, wherePart):
                    if wherePart is None:
                        return True

                    or_segments = [seg.strip() for seg in wherePart.split(" OR ")]

                    for or_part in or_segments:
                        and_parts = [a.strip() for a in or_part.split(" AND ")]
                        all_and_ok = True

                        for cond in and_parts:
                            if ">=" in cond:
                                col, val = cond.split(">="); op = ">="
                            elif "<=" in cond:
                                col, val = cond.split("<="); op = "<="
                            elif "!=" in cond:
                                col, val = cond.split("!="); op = "!="
                            elif ">" in cond:
                                col, val = cond.split(">"); op = ">"
                            elif "<" in cond:
                                col, val = cond.split("<"); op = "<"
                            elif " LIKE " in cond:
                                col, val = cond.split(" LIKE "); op = "LIKE"; val = val.strip("'").strip('"')
                            else:
                                col, val = cond.split("="); op = "="

                            col = col.strip().upper()
                            val = val.strip()

                            if col not in header:
                                all_and_ok = False
                                break

                            idx = header.index(col)
                            cell = row[idx]

                            if op == "LIKE":
                                if val.lower() not in cell.lower():
                                    all_and_ok = False
                                continue

                            try:
                                left = float(cell); right = float(val)
                            except:
                                left = cell; right = val

                            if op == "="  and not (left == right): all_and_ok = False
                            if op == "!=" and not (left != right): all_and_ok = False
                            if op == ">"  and not (left >  right): all_and_ok = False
                            if op == "<"  and not (left <  right): all_and_ok = False
                            if op == ">=" and not (left >= right): all_and_ok = False
                            if op == "<=" and not (left <= right): all_and_ok = False

                        if all_and_ok:
                            return True

                    return False

                newRows = []
                deleted = 0
                for row in rows:
                    if row_matches(row, wherePart):
                        deleted += 1
                    else:
                        newRows.append(row)

                with open(filePath, "w", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(header)
                    writer.writerows(newRows)

                query = [*f"{deleted} ROWS DELETED", cursor]
                return

            except Exception as e:
                query = [*f"ERROR IN DELETE ROWS: {e}", cursor]
                return
            
    elif Query.startswith("SELECT") :
        addToUndoStack()

        if state == 2 and openedTable is not None:
            try:
                rest = Query[len("SELECT "):].strip()

                if " WHERE " in rest:
                    selectPart, wherePart = rest.split(" WHERE ", 1)
                else:
                    selectPart = rest
                    wherePart = None

                if selectPart.strip() == "*":
                    selectedColumns = None
                    if wherePart is None :
                        if os.path.exists(os.path.join("DATABASES", "RESULT.csv")) :
                            os.remove(os.path.join("DATABASES", "RESULT.csv"))
                        query = [cursor]
                        return
                else:
                    selectedColumns = [col.strip().upper() for col in selectPart.split(",")]

                filePath = os.path.join('DATABASES', openedDatabase.name, f"{openedTable.name}.csv")

                with open(filePath, 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    all_data = [row for row in reader]

                header = all_data[0]
                rows = all_data[1:]

                for i in range(len(rows)):
                    if len(rows[i]) < len(header):
                        rows[i] += [""] * (len(header) - len(rows[i]))

                if selectedColumns is None:
                    selectedIndexes = list(range(len(header)))
                    selectedHeader = header
                else:
                    selectedIndexes = [header.index(col) for col in selectedColumns]
                    selectedHeader = selectedColumns

                if wherePart is not None:
                    or_segments = [seg.strip() for seg in wherePart.split(" OR ")]

                    filteredRows = []

                    for row in rows:
                        rowMatchesOR = False

                        for or_part in or_segments:
                            and_parts = [a.strip() for a in or_part.split(" AND ")]

                            all_AND_match = True

                            for cond in and_parts:
                                if ">=" in cond:
                                    col, val = cond.split(">=")
                                    op = ">="
                                elif "<=" in cond:
                                    col, val = cond.split("<=")
                                    op = "<="
                                elif "!=" in cond:
                                    col, val = cond.split("!=")
                                    op = "!="
                                elif ">" in cond:
                                    col, val = cond.split(">")
                                    op = ">"
                                elif "<" in cond:
                                    col, val = cond.split("<")
                                    op = "<"
                                elif " LIKE " in cond:
                                    col, val = cond.split(" LIKE ")
                                    op = "LIKE"
                                    val = val.strip("'").strip('"')
                                else:
                                    col, val = cond.split("=")
                                    op = "="

                                col = col.strip().upper()
                                val = val.strip()

                                if col not in header:
                                    all_AND_match = False
                                    break

                                whereIndex = header.index(col)
                                cell = row[whereIndex]

                                if op == "LIKE":
                                    if val.lower() not in cell.lower():
                                        all_AND_match = False
                                    continue

                                try:
                                    left = float(cell)
                                    right = float(val)
                                except:
                                    left = cell
                                    right = val

                                if op == "=" and not (left == right):
                                    all_AND_match = False
                                elif op == "!=" and not (left != right):
                                    all_AND_match = False
                                elif op == ">" and not (left > right):
                                    all_AND_match = False
                                elif op == "<" and not (left < right):
                                    all_AND_match = False
                                elif op == ">=" and not (left >= right):
                                    all_AND_match = False
                                elif op == "<=" and not (left <= right):
                                    all_AND_match = False

                            if all_AND_match:
                                rowMatchesOR = True
                                break

                        if rowMatchesOR:
                            filteredRows.append(row)

                else:
                    filteredRows = rows

                result = [selectedHeader]
                for row in filteredRows:
                    result.append([row[i] for i in selectedIndexes])

                resultPath = os.path.join('DATABASES', "RESULT.csv")

                with open(resultPath, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(result)

                query = [f"{len(result)-1} ROWS FOUND", cursor]
                return

            except Exception as e:
                query = [*f"ERROR IN SELECT: {e}", cursor]
                return

    elif Query.startswith("FOCUS <ALL>") :
        addToUndoStack()

        COLS = 4
        H_SPACING = 200
        V_SPACING = 150

        if state == 0:
            items = Databases
        else:
            items = openedDatabase.tables

        if not items:
            return

        centerX = cameraX + (screen.get_width() / 2) / zoomFactor
        centerY = cameraY + (screen.get_height() / 2) / zoomFactor

        itemCount = len(items)

        rows = math.ceil(itemCount / COLS)

        totalWidth = (COLS - 1) * H_SPACING
        totalHeight = (rows - 1) * V_SPACING

        startX = centerX - totalWidth / 2
        startY = centerY - totalHeight / 2

        index = 0
        for r in range(rows):
            for c in range(COLS):
                if index >= itemCount:
                    break

                item = items[index]
                rect = item.getRect()

                item.x = startX + c * H_SPACING - rect.width / (2 * zoomFactor)
                item.y = startY + r * V_SPACING

                index += 1
    
    elif Query.startswith("DELETE"):
        addToUndoStack()

        parts = Query.partition(" ")

        if state == 0 :
            dbName = parts[2]
            dbToDelete = None
            for db in Databases:
                if db.name == dbName:
                    dbToDelete = db
                    break
            if dbToDelete:
                Databases.remove(dbToDelete)
                shutil.rmtree(os.path.join('DATABASES', dbToDelete.name))
        if state == 1 :
            tableName = parts[2]
            tableToDelete = None
            for table in openedDatabase.tables:
                if table.name == tableName:
                    tableToDelete = table
                    break
            if tableToDelete:
                openedDatabase.tables.remove(tableToDelete)
                os.remove(os.path.join('DATABASES', openedDatabase.name, f"{tableToDelete.name}.csv"))

    elif Query.startswith("OPEN"):
        parts = Query.partition(" ")

        if state == 0 :
            dbName = parts[2]
            for db in Databases:
                if db.name == dbName:
                    state = 1
                    openedDatabase = db
                    break
    
    elif Query.startswith("FOCUS"):
        addToUndoStack()

        parts = Query.partition(" ")

        if state == 0 :
            dbName = parts[2]
            for db in Databases:
                if db.name == dbName:
                    db.x = cameraX + (screen.get_width() / 2) / zoomFactor - db.getRect().width / (2 * zoomFactor)
                    db.y = cameraY + (screen.get_height() / 2) / zoomFactor
                    break
        if state == 1 :
            tableName = parts[2]
            for table in openedDatabase.tables:
                if table.name == tableName:
                    table.x = cameraX + (screen.get_width() / 2) / zoomFactor - table.getRect().width / (2 * zoomFactor)
                    table.y = cameraY + (screen.get_height() / 2) / zoomFactor
                    break

    elif Query.startswith("RENAME"):
        addToUndoStack()

        parts = Query.partition(" ")

        if state == 0 :
            oldName = parts[2].split(" TO ")[0]
            newName = parts[2].split(" TO ")[1]

            for db in Databases:
                if db.name == oldName:
                    oldPath = os.path.join('DATABASES', db.name)
                    newPath = os.path.join('DATABASES', newName)

                    if not os.path.exists(newPath):
                        os.rename(oldPath, newPath)
                        db.name = newName
                    else :
                        query = [*'DATABASE ALREADY EXISTS', cursor]
                        return
                    break

                elif Databases.index(db) == len(Databases) - 1 :
                    query = [*'DATABASE NOT FOUND', cursor]
                    return

        elif state == 1 :
            oldName = parts[2].split(" TO ")[0]
            newName = parts[2].split(" TO ")[1]

            for table in openedDatabase.tables:
                if table.name == oldName:
                    oldPath = os.path.join('DATABASES', openedDatabase.name, f"{table.name}.csv")
                    newPath = os.path.join('DATABASES', openedDatabase.name, f"{newName}.csv")

                    if not os.path.exists(newPath):
                        os.rename(oldPath, newPath)
                        table.name = newName
                    else :
                        query = [*'TABLE ALREADY EXISTS', cursor]
                        return
                    break

                elif openedDatabase.tables.index(table) == len(openedDatabase.tables) - 1 :
                    query = [*'TABLE NOT FOUND', cursor]
                    return
                
    elif Query.startswith("OPEN"):
        parts = Query.partition(" ")

        if state == 0 :
            dbName = parts[2]
            for db in Databases:
                if db.name == dbName:
                    state = 1
                    openedDatabase = db
                    break

                elif Databases.index(db) == len(Databases) - 1:
                    query = [*'DATABASE NOT FOUND', cursor]
                    return
                
    elif Query.startswith("ADD FIELDS"):
        addToUndoStack()
        if state == 1 and openedDatabase is not None:
            try:
                parts = Query.split("ADD FIELDS TO", 1)

                rest = parts[1].strip()

                tableName = rest[:rest.find("(")].strip()
                fieldsStr = rest[rest.find("(")+1:-1].strip()

                newFields = [field.strip() for field in fieldsStr.split(',') if field.strip()]

                if len(newFields) != len(set(newFields)):
                    query = [*'DUPLICATE FIELDS IN QUERY', cursor]
                    return

                targetTable = None
                for table in openedDatabase.tables:
                    if table.name == tableName:
                        targetTable = table
                        break

                if targetTable:
                    for field in newFields:
                        if field in targetTable.columns:
                            query = [*f"FIELD '{field}' ALREADY EXISTS", cursor]
                            return

                    targetTable.columns.extend(newFields)
                    targetTable.types.extend(['I'] * len(newFields))

                    filePath = os.path.join('DATABASES', openedDatabase.name, f"{targetTable.name}.csv")
                    with open(filePath, 'r+', newline='') as csvfile:
                        reader = csv.reader(csvfile)
                        writer = csv.writer(csvfile)
                        try:
                            header = next(reader)
                        except StopIteration:
                            header = []

                        csvfile.seek(0)
                        writer.writerow(header + newFields)
                else:
                    query = [*'TABLE NOT FOUND', cursor]
                    return

            except IndexError:
                query = [*'INVALID SYNTAX', cursor]
                return

    else :
        query = [*'INVALID QUERY', cursor]
        return
    
    query = [cursor]

initialState = {
    'Databases': copy.deepcopy(Databases),
    'openedDatabase_name': openedDatabase.name if openedDatabase else None,
    'openedTable_name': openedTable.name if openedTable else None,
    'state': state,
    'file_system': {}
}

for root, dirs, files in os.walk('DATABASES'):
    for name in dirs:
        path = os.path.join(root, name)
        initialState['file_system'][path] = None
    for name in files:
        path = os.path.join(root, name)
        try:
            with open(path, 'r', newline='', encoding='utf-8') as f:
                initialState['file_system'][path] = f.read()
        except IOError: continue

undoStack.append(initialState)

scrollValueVertical = 0
scrollValueHorizontal = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN :
            if pygame.mouse.get_pressed()[0] :
                if selectedDatabase != None :
                    oldPath = os.path.join('DATABASES', oldName)
                    newPath = os.path.join('DATABASES', selectedDatabase.name)

                    if (os.path.exists(newPath) and oldPath != newPath) or selectedDatabase.name == '':
                        selectedDatabase.name = oldName
                    else:
                        addToUndoStack()
                        os.rename(oldPath, newPath)

                if selectedTable != None :
                    oldPath = os.path.join('DATABASES', openedDatabase.name, f"{oldName}.csv")
                    newPath = os.path.join('DATABASES', openedDatabase.name, f"{selectedTable.name}.csv")

                    if (os.path.exists(newPath) and oldPath != newPath) or selectedTable.name == '':
                        selectedTable.name = oldName
                    else:
                        addToUndoStack()
                        os.rename(oldPath, newPath)

                    if selectedTable.selectedColumnIndex != None :
                        colIndex = selectedTable.selectedColumnIndex
                        newName = selectedTable.columns[colIndex].strip()

                        filePath = os.path.join('DATABASES', openedDatabase.name, f"{selectedTable.name}.csv")
                        with open(filePath, 'r', newline='') as csvfile:
                            reader = csv.reader(csvfile)
                            try:
                                header = next(reader)
                            except StopIteration:
                                header = []

                        oldName = header[colIndex] if colIndex < len(header) else ''

                        if newName == '' or newName in [col for i, col in enumerate(selectedTable.columns) if i != colIndex]:
                            selectedTable.columns[colIndex] = oldName

                        else:
                            if header:
                                header[colIndex] = newName
                            else:
                                header = [newName]

                            with open(filePath, 'r', newline='') as csvfile:
                                reader = csv.reader(csvfile)
                                all_data = [row for row in reader]
                            if all_data:
                                all_data[0] = header
                            else:
                                all_data = [header]

                            with open(filePath, 'w', newline='') as csvfile:
                                writer = csv.writer(csvfile)
                                writer.writerows(all_data)

                if enterQueryIconRect.collidepoint(event.pos):
                    queryMode = True
                else:
                    if not (Toolbar.collidepoint(event.pos) and queryMode == True) :
                        query = [cursor]
                        queryMode = False
                
                if Toolbar.collidepoint(event.pos) and queryMode == False:
                    if createIconRect.collidepoint(event.pos):
                        if state == 0 :
                            addToUndoStack()

                            newDBName = "NEW_DATABASE"
                            count = 1

                            while os.path.exists(os.path.join('DATABASES', newDBName)):
                                newDBName = f"NEW_DATABASE_{count}"
                                count += 1

                            newDB = Database(newDBName, cameraX + (screen.get_width() / 2) / zoomFactor, cameraY + (screen.get_height() / 2) / zoomFactor, scale=False)

                            Databases.append(newDB)

                            selectedDatabase = newDB
                            oldName = newDBName

                            os.makedirs(os.path.join('DATABASES', newDBName))

                        else :
                            addToUndoStack()

                            newTableName = "NEW_TABLE"
                            count = 1

                            existingTableNames = [table.name for table in openedDatabase.tables]

                            while newTableName in existingTableNames:
                                newTableName = f"{newTableName}_{count}"
                                count += 1

                            newTable = Table(newTableName, [], cameraX + (screen.get_width() / 2) / zoomFactor, cameraY + (screen.get_height() / 2) / zoomFactor, scale=False)

                            openedDatabase.tables.append(newTable)

                            open(os.path.join('DATABASES', openedDatabase.name, f"{newTableName}.csv"), 'w').close()

                    elif deleteIconRect.collidepoint(event.pos):
                        if selectedDatabase != None:
                            addToUndoStack()

                            Databases.remove(selectedDatabase)
                            shutil.rmtree(os.path.join('DATABASES', selectedDatabase.name))

                            selectedDatabase = None

                        elif selectedTable != None :
                            addToUndoStack()

                            openedDatabase.tables.remove(selectedTable)
                            os.remove(os.path.join('DATABASES', openedDatabase.name, selectedTable.name + '.csv'))
                            
                            selectedTable = None

                    elif openIconRect.collidepoint(event.pos):
                        if selectedDatabase != None:
                            addToUndoStack()

                            state = 1
                            openedDatabase = selectedDatabase
                            selectedDatabase = None

                        elif selectedTable != None :
                            addToUndoStack()

                            state = 2
                            openedTable = selectedTable
                            selectedTable = None

                    elif backIconRect.collidepoint(event.pos):
                        if state == 1 :
                            state = 0
                            openedDatabase = None
                            selectedTable = None
                        else :
                            state = 1
                            openedTable = None
                    
                    elif undoIconRect.collidepoint(event.pos):
                        undo()

                    elif redoIconRect.collidepoint(event.pos):
                        redo()

                else :
                    mousedown = True

                prevMX = pygame.mouse.get_pos()[0]
                prevMY = pygame.mouse.get_pos()[1]

                prevCX = cameraX
                prevCY = cameraY

                if state == 0 :
                    for i in Databases[::-1] :
                        if i.getRect().collidepoint(event.pos) and queryMode == False:
                            selectedDatabase = i

                            dragOffsetX = pygame.mouse.get_pos()[0] - i.getRect().x
                            dragOffsetY = pygame.mouse.get_pos()[1] - i.getRect().y

                            oldName = i.name

                            if selectedDatabase == i:
                                if pygame.time.get_ticks() - lastClickTime <= doubleClickThreshold:
                                    state = 1
                                    selectedDatabase = None
                                    openedDatabase = i

                                    for table in openedDatabase.tables :
                                        table.lastClickTime = -10000

                            lastClickTime = pygame.time.get_ticks()

                            break

                        selectedDatabase = None

                elif state == 1 :
                    clickedOnTableComp = False
                    for i in openedDatabase.tables[::-1] :
                        if i.getRect().collidepoint(event.pos) and queryMode == False:
                            clickedOnTableComp = True

                            curTime = pygame.time.get_ticks()

                            plusButton, minusButton = i.getButtonsRects()

                            if plusButton.collidepoint(event.pos):
                                addToUndoStack()

                                newFieldBase = "NEW_FIELD"
                                newFieldName = newFieldBase
                                count = 1
                                while newFieldName in i.columns:
                                    newFieldName = f"{newFieldBase}_{count}"
                                    count += 1
                                i.columns.append(newFieldName)
                                i.types.append("I")
                                
                                filePath = os.path.join('DATABASES', openedDatabase.name, f"{i.name}.csv")
                                with open(filePath, 'r+', newline='') as csvfile:
                                    reader = csv.reader(csvfile)
                                    try:
                                        header = next(reader)
                                    except StopIteration:
                                        header = []
                                    csvfile.seek(0)
                                    writer = csv.writer(csvfile)
                                    writer.writerow(header + [newFieldName])
                                selectedTable = None

                            elif minusButton.collidepoint(event.pos) and i.selectedColumnIndex is not None and len(i.columns) > 0:
                                addToUndoStack()
                                indexToDelete = i.selectedColumnIndex
                                
                                filePath = os.path.join('DATABASES', openedDatabase.name, f"{i.name}.csv")
                                with open(filePath, 'r', newline='') as csvfile:
                                    reader = csv.reader(csvfile)
                                    all_data = [row for row in reader]
                                
                                new_data = [[item for idx, item in enumerate(row) if idx != indexToDelete] for row in all_data]

                                with open(filePath, 'w', newline='') as csvfile:
                                    writer = csv.writer(csvfile)
                                    writer.writerows(new_data)

                                i.columns.pop(indexToDelete)
                                i.types.pop(indexToDelete)
                                i.selectedColumnIndex = None
                                selectedTable = None

                            clickedColumn = False

                            for columnIndex in range(len(i.columns)):
                                colRect = i.getColumnRect(columnIndex)
                                colTypeButtonRect = i.getTypeButtonRect(columnIndex)

                                if colRect.collidepoint(event.pos):
                                    isDoubleClick = (
                                        lastClickedTable is i and
                                        lastClickedCol == columnIndex and
                                        curTime - lastClickTime <= doubleClickThreshold
                                    )

                                    lastClickTime = curTime
                                    lastClickedTable = i
                                    lastClickedCol = columnIndex

                                    for table in openedDatabase.tables:
                                        if table is not i:
                                            table.selectedColumnIndex = None

                                    if isDoubleClick:
                                        if i.primaryKeyIndex == columnIndex:
                                            i.primaryKeyIndex = None
                                        elif columnIndex not in [fk["column"] for fk in i.foreignKeys]:
                                            i.primaryKeyIndex = columnIndex
                                        else :
                                            for fk in i.foreignKeys :
                                                if fk["column"] == columnIndex :
                                                    i.foreignKeys.remove(fk)
                                                    break
                                    else:
                                        i.selectedColumnIndex = columnIndex

                                    selectedTable = None
                                    clickedColumn = True
                                    break

                                if colTypeButtonRect.collidepoint(event.pos):
                                    addToUndoStack()

                                    if i.types[columnIndex] == "I" :
                                        i.types[columnIndex] = "S"
                                    elif i.types[columnIndex] == "S" :
                                        i.types[columnIndex] = "F"
                                    elif i.types[columnIndex] == "F" :
                                        i.types[columnIndex] = "B"
                                    elif i.types[columnIndex] == "B" :
                                        i.types[columnIndex] = "I"

                                    for fk in i.foreignKeys :
                                        if fk["column"] == columnIndex :
                                            i.foreignKeys.remove(fk)
                                            break

                                    for table in openedDatabase.tables:
                                        for fk in table.foreignKeys:
                                            if fk["ref_table"] == i.name and fk["ref_column"] == columnIndex:
                                                table.foreignKeys.remove(fk)

                                    i.lastClickTime = 0

                            if not clickedColumn :
                                i.selectedColumnIndex = None

                            if i.lastClickTime != 0 and (curTime - i.lastClickTime <= doubleClickThreshold) and not plusButton.collidepoint(event.pos) and not minusButton.collidepoint(event.pos) and not clickedColumn:
                                state = 2
                                openedTable = selectedTable
                                selectedTable = None
                                i.lastClickTime = 0
                                break

                            i.lastClickTime = curTime

                            selectedTable = i

                            dragOffsetX = pygame.mouse.get_pos()[0] - i.getRect().x
                            dragOffsetY = pygame.mouse.get_pos()[1] - i.getRect().y

                            oldName = i.name

                            curTime = pygame.time.get_ticks()

                            break
                    
                    if not clickedOnTableComp:
                        selectedTable = None
                        for table in openedDatabase.tables:
                            table.selectedColumnIndex = None
        if event.type == pygame.MOUSEBUTTONUP :
            if draggingColumn != None :
                for i in openedDatabase.tables :
                    if i.getRect().collidepoint(pygame.mouse.get_pos()):
                        for c in i.columns :
                            if i.getColumnRect(i.columns.index(c)).collidepoint(event.pos) and selectedTable.types[draggingColumn] == i.types[i.columns.index(c)] :
                                selectedTable.addForeignKey(draggingColumn, i.name, i.columns.index(c))

            mousedown = False
            dragging = 1
            draggingColumn = None

        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0 and state != 2:
                zoomIn()
            elif event.y < 0 and state != 2:
                zoomOut()

            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    scrollValueHorizontal -= event.y
            else:
                scrollValueVertical -= event.y

        if event.type == pygame.VIDEORESIZE:
            vignette = createVignette(intensity=255, radiusFactor=2)

        if event.type == pygame.KEYDOWN :
            if event.key == pygame.K_f and queryMode == False and selectedDatabase == None and selectedTable == None :
                if screen.get_height() >= screenHeight and screen.get_width() >= screenWidth :
                    screen = pygame.display.set_mode((screenWidth - 10, screenHeight - 50), pygame.RESIZABLE)
                else :
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

            if selectedDatabase != None and state == 0 and queryMode == False:
                if event.key == pygame.K_DELETE :
                    selectedDatabase.name = ''
                
                elif event.key == pygame.K_BACKSPACE :
                    selectedDatabase.name = selectedDatabase.name[:-1]
                
                elif event.key == pygame.K_RETURN :
                    oldPath = os.path.join('DATABASES', oldName)
                    newPath = os.path.join('DATABASES', selectedDatabase.name)

                    if (os.path.exists(newPath) and oldPath != newPath) or selectedDatabase.name == '':
                        selectedDatabase.name = oldName
                    else:
                        addToUndoStack()
                        os.rename(oldPath, newPath)

                    selectedDatabase = None

                elif len(event.unicode) == 1 and event.unicode.isprintable() :
                    selectedDatabase.name += event.unicode.upper()

            if selectedTable != None and state == 1 and queryMode == False and selectedTable.selectedColumnIndex == None:
                if event.key == pygame.K_DELETE:
                    selectedTable.name = ''

                elif event.key == pygame.K_BACKSPACE:
                    selectedTable.name = selectedTable.name[:-1]

                elif event.key == pygame.K_RETURN:
                    oldPath = os.path.join('DATABASES', openedDatabase.name, f"{oldName}.csv")
                    newPath = os.path.join('DATABASES', openedDatabase.name, f"{selectedTable.name}.csv")

                    if (os.path.exists(newPath) and oldPath != newPath) or selectedTable.name == '':
                        selectedTable.name = oldName
                    else:
                        addToUndoStack()
                        os.rename(oldPath, newPath)

                    selectedTable = None

                elif len(event.unicode) == 1 and event.unicode.isprintable():
                    selectedTable.name += event.unicode.upper()

            if selectedTable != None and selectedTable.selectedColumnIndex != None and state == 1 and queryMode == False:
                colIndex = selectedTable.selectedColumnIndex

                if event.key == pygame.K_DELETE:
                    selectedTable.columns[colIndex] = ''

                elif event.key == pygame.K_BACKSPACE:
                    selectedTable.columns[colIndex] = selectedTable.columns[colIndex][:-1]

                elif event.key == pygame.K_RETURN:
                    colIndex = selectedTable.selectedColumnIndex
                    newName = selectedTable.columns[colIndex].strip()

                    filePath = os.path.join('DATABASES', openedDatabase.name, f"{selectedTable.name}.csv")
                    with open(filePath, 'r', newline='') as csvfile:
                        reader = csv.reader(csvfile)
                        try:
                            header = next(reader)
                        except StopIteration:
                            header = []

                    old_name = header[colIndex] if colIndex < len(header) else ''

                    if newName == '' or newName in [col for i, col in enumerate(selectedTable.columns) if i != colIndex]:
                        selectedTable.columns[colIndex] = oldName

                    else:
                        if header:
                            header[colIndex] = newName
                        else:
                            header = [newName]

                        with open(filePath, 'r', newline='') as csvfile:
                            reader = csv.reader(csvfile)
                            all_data = [row for row in reader]

                        if all_data:
                            all_data[0] = header
                        else:
                            all_data = [header]

                        with open(filePath, 'w', newline='') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerows(all_data)

                    selectedTable.selectedColumnIndex = None

                elif len(event.unicode) == 1 and event.unicode.isprintable():
                    selectedTable.columns[colIndex] += event.unicode.upper()

            if queryMode :
                if event.key == pygame.K_DELETE :
                    query = [cursor]

                if event.key == pygame.K_BACKSPACE :
                    for i in range(len(query)) :
                        if query[i] == cursor :
                            cursorPos = i
                            break
                    if cursorPos > 0 :
                        query.pop(cursorPos - 1)

                if event.key == pygame.K_LEFT :
                    for i in range(len(query)) :
                        if query[i] == cursor :
                            cursorPos = i
                            break
                    if cursorPos > 0 :
                        query.pop(cursorPos)
                        query.insert(cursorPos - 1, cursor)

                elif event.key == pygame.K_RIGHT :
                    for i in range(len(query)) :
                        if query[i] == cursor :
                            cursorPos = i
                            break
                    if cursorPos < len(query) - 1 :
                        query.pop(cursorPos)
                        query.insert(cursorPos + 1, cursor)

                elif event.key == pygame.K_RETURN :
                    q = "".join(query).replace(cursor, '').strip()
                    queryExecutor(q)

                else :
                    if len(event.unicode) == 1 and event.unicode.isprintable() :
                        cursorPos = query.index(cursor)

                        for i in range(len(query)) :
                            if query[i] == cursor :
                                cursorPos = i
                                break

                        query.insert(cursorPos, event.unicode.upper())

        if event.type == pygame.QUIT:
            if os.path.exists(os.path.join("DATABASES", "RESULT.csv")) :
                os.remove(os.path.join("DATABASES", "RESULT.csv"))

            f = open("save.txt", "wb")

            pickle.dump(Databases, f)

            f.close()

            running = False

    screen.fill((28, 38, 36))

    center = (screen.get_width()/2, screen.get_height()/2)

    keys = pygame.key.get_pressed()
    if not queryMode:
        if keys[pygame.K_LEFT]:  cameraX -= respValX(25)
        if keys[pygame.K_RIGHT]: cameraX += respValX(25)
        if keys[pygame.K_UP]:    cameraY -= respValY(25)
        if keys[pygame.K_DOWN]:  cameraY += respValY(25)

    viewWidth = screen.get_width() / zoomFactor
    viewHeight = screen.get_height() / zoomFactor

    cameraX = max(-2000, min(cameraX, 2000 - viewWidth))
    cameraY = max(-1000, min(cameraY, 1000 - viewHeight))

    for i in range(0, screen.get_width() + 2 * respValX(gridSpacing), respValX(gridSpacing)) :
        for j in range(0, screen.get_height() + 2 * respValY(gridSpacing), respValY(gridSpacing)) :
            pygame.draw.circle(screen, (dragging*60,dragging*60,dragging*60), (i, j), 1)

    if mousedown and (selectedDatabase != None or selectedTable != None):
        if state == 0 :
            selectedDatabase.x = (pygame.mouse.get_pos()[0] - dragOffsetX) / zoomFactor + cameraX
            selectedDatabase.y = (pygame.mouse.get_pos()[1] - dragOffsetY) / zoomFactor + cameraY

        elif state == 1 and selectedTable.selectedColumnIndex == None :
            selectedTable.x = (pygame.mouse.get_pos()[0] - dragOffsetX) / zoomFactor + cameraX
            selectedTable.y = (pygame.mouse.get_pos()[1] - dragOffsetY) / zoomFactor + cameraY

    fkColor = (27, 117, 158)

    if state != 2 :
        if os.path.exists(os.path.join("DATABASES", "RESULT.csv")) :
            os.remove(os.path.join("DATABASES", "RESULT.csv"))

    if state == 0:
        for i in Databases :
            i.draw()

    elif state == 1:
        for db in Databases:
            if db == openedDatabase:
                for table in db.tables:
                    table.draw()
                break
        
        for db in Databases:
            if db == openedDatabase:
                for table in db.tables:
                    for fk in table.foreignKeys:
                        startRect = table.getColumnRect(fk["column"])
                        target_table = next((t for t in db.tables if t.name == fk["ref_table"]), None)

                        if not target_table or target_table == table:
                            continue

                        if target_table.types[fk["ref_column"]] != table.types[fk["column"]] :
                            continue

                        endRect = target_table.getColumnRect(fk["ref_column"])

                        startPos = (startRect.x + startRect.width, startRect.y + startRect.height/2)
                        endPos = (endRect.x - respValX(22.5, False)*zoomFactor, endRect.y + endRect.height/2)

                        angle = math.atan2((endPos[1] - startPos[1]), (endPos[0] - startPos[0]))

                        pygame.draw.circle(screen, fkColor, startPos, 5)
                        
                        pygame.draw.polygon(screen, fkColor, [endPos, (15*math.cos(math.pi + angle + 0.75) + endPos[0], 15*math.sin(math.pi + angle + 0.75) + endPos[1]), (15*math.cos(math.pi + angle - 0.75) + endPos[0], 15*math.sin(math.pi + angle - 0.75) + endPos[1])])

                        pygame.draw.line(screen, fkColor, startPos, endPos, 3)

    if mousedown and selectedDatabase == None and queryMode == False :
        colSelected = False

        if openedDatabase != None and selectedTable != None  :
            if selectedTable.selectedColumnIndex != None :
                colSelected = True

        if selectedTable == None and not colSelected :
            cameraX = -(pygame.mouse.get_pos()[0] - (prevMX)) / zoomFactor + prevCX
            cameraY = -(pygame.mouse.get_pos()[1] - (prevMY)) / zoomFactor + prevCY
            dragging = 1.5

        colInd = None

        if openedDatabase != None and selectedTable != None :
            if selectedTable.selectedColumnIndex != None :
                colInd = selectedTable.selectedColumnIndex

        if colInd != None and not selectedTable.getRect().collidepoint(pygame.mouse.get_pos()) :
            tRect = selectedTable.getColumnRect(selectedTable.selectedColumnIndex)
            pygame.draw.circle (screen, fkColor, (tRect.x + tRect.width, tRect.y + tRect.height/2), 5)
            pygame.draw.line(screen, fkColor, (tRect.x + tRect.width, tRect.y + tRect.height/2), pygame.mouse.get_pos(), math.floor(3 * zoomFactor) + 1)

            angle = math.atan2((pygame.mouse.get_pos()[1] - (tRect.y + tRect.height/2)), (pygame.mouse.get_pos()[0] - (tRect.x + tRect.width)))

            pygame.draw.polygon(screen, fkColor, [pygame.mouse.get_pos(), (15*math.cos(math.pi + angle + 0.75) + pygame.mouse.get_pos()[0], 15*math.sin(math.pi + angle + 0.75) + pygame.mouse.get_pos()[1]), (15*math.cos(math.pi + angle - 0.75) + pygame.mouse.get_pos()[0], 15*math.sin(math.pi + angle - 0.75) + pygame.mouse.get_pos()[1])])
            draggingColumn = colInd

    toolabarSurface = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)

    if pygame.mouse.get_pos()[1] > center[1] + respValY(420) and mousedown == False:
        fy = center[1] + respValY(440)
        start = pygame.time.get_ticks()
    elif pygame.time.get_ticks() - start > 3000 and queryMode == False :
        fy = center[1] + respValY(750)

    if ty != fy :
        if ty < fy :
            ty += abs(ty-fy) * 0.025
        if ty > fy :
            ty -= abs(ty-fy) * 0.5

    Toolbar = pygame.draw.rect(toolabarSurface, (201,212,199, (int(not queryMode) * 50) + (int(queryMode) * 255)), (center[0]-respValX(480), ty, respValX(960), respValY(75)), border_radius=respValX(50))

    if queryMode:
        for i in range(len(query)):
            if query[i] == cursor:
                cursorPos = i
                break
        q = "".join(query[-1*46:cursorPos]) + "".join(query[cursorPos:cursorPos+46])
        font = pygame.font.SysFont(mainFont, int(respValY(40, False)), bold=True)
        queryText = font.render(q, True, "BLACK")

        queryTextRect = pygame.Rect(center[0]-respValX(455), center[1] + respValY(462), respValX(960), respValY(75))

        toolabarSurface.blit(queryText, queryTextRect.topleft)

    if not queryMode:
        iconY = ty + respValY(10)
        iconW = respValX(55)
        iconH = respValY(55)

        backIconRect = pygame.Rect(center[0], iconY, iconW, iconH)
        createIconRect = pygame.Rect(center[0], iconY, iconW, iconH)
        deleteIconRect = pygame.Rect(center[0], iconY, iconW, iconH)
        openIconRect = pygame.Rect(center[0], iconY, iconW, iconH)
        undoIconRect = pygame.Rect(center[0], iconY, iconW, iconH)
        redoIconRect = pygame.Rect(center[0], iconY, iconW, iconH)
        enterQueryIconRect = pygame.Rect(center[0], iconY, iconW, iconH)

        icons = [createIconRect, deleteIconRect, openIconRect, undoIconRect, redoIconRect, enterQueryIconRect]

        if state == 1 or state == 2 :
            icons.insert(0, backIconRect)

        if state == 2 :
            icons.pop(1)
            icons.pop(2)
            icons.pop(3)

        for i in range(len(icons)):
            icons[i].x = center[0] - (len(icons) * iconW + (len(icons) - 1) * (respValX(980/len(icons)) - iconW)) / 2 + i * respValX(980/len(icons))
            pygame.draw.rect(toolabarSurface, (201,212,199, (int(not icons[i].collidepoint(pygame.mouse.get_pos())) * 150 + int(icons[i].collidepoint(pygame.mouse.get_pos())) * 255)), icons[i], border_radius=respValX(10))

            if icons[i].collidepoint(pygame.mouse.get_pos()) :
                if icons[i] == enterQueryIconRect :
                    font = pygame.font.SysFont(mainFont, int(respValY(25, False)), bold=False)
                    surface = font.render("ENTER QUERY", True, (255, 255, 255))
                    screen.blit(surface, (icons[i].x + icons[i].width / 2 - surface.get_width() / 2, icons[i].y - respValY(35), respValX(2000), respValY(1000)))
                
                elif icons[i] == createIconRect :
                    font = pygame.font.SysFont(mainFont, int(respValY(25, False)), bold=False)
                    if state == 0 :
                        surface = font.render("CREATE DATABASE", True, (255, 255, 255))
                    if state == 1 :
                        surface = font.render("CREATE TABLE", True, (255, 255, 255))
                    screen.blit(surface, (icons[i].x + icons[i].width / 2 - surface.get_width() / 2, icons[i].y - respValY(35), respValX(2000), respValY(1000)))

                elif icons[i] == deleteIconRect :
                    font = pygame.font.SysFont(mainFont, int(respValY(25, False)), bold=False)
                    if state == 0 :
                        surface = font.render("DELETE DATABASE", True, (255, 255, 255))
                    if state == 1 :
                        surface = font.render("DELETE TABLE", True, (255, 255, 255))
                    screen.blit(surface, (icons[i].x + icons[i].width / 2 - surface.get_width() / 2, icons[i].y - respValY(35), respValX(2000), respValY(1000)))
                
                elif icons[i] == openIconRect :
                    font = pygame.font.SysFont(mainFont, int(respValY(25, False)), bold=False)
                    if state == 0 :
                        surface = font.render("OPEN DATABASE", True, (255, 255, 255))
                    if state == 1 :
                        surface = font.render("OPEN TABLE", True, (255, 255, 255))
                    screen.blit(surface, (icons[i].x + icons[i].width / 2 - surface.get_width() / 2, icons[i].y - respValY(35), respValX(2000), respValY(1000)))

                elif icons[i] == backIconRect :
                    font = pygame.font.SysFont(mainFont, int(respValY(25, False)), bold=False)
                    surface = font.render("BACK", True, (255, 255, 255))
                    screen.blit(surface, (icons[i].x + icons[i].width / 2 - surface.get_width() / 2, icons[i].y - respValY(35), respValX(2000), respValY(1000)))

                elif icons[i] == undoIconRect :
                    font = pygame.font.SysFont(mainFont, int(respValY(25, False)), bold=False)
                    surface = font.render("UNDO", True, (255, 255, 255))
                    screen.blit(surface, (icons[i].x + icons[i].width / 2 - surface.get_width() / 2, icons[i].y - respValY(35), respValX(2000), respValY(1000)))

                elif icons[i] == redoIconRect :
                    font = pygame.font.SysFont(mainFont, int(respValY(25, False)), bold=False)
                    surface = font.render("REDO", True, (255, 255, 255))
                    screen.blit(surface, (icons[i].x + icons[i].width / 2 - surface.get_width() / 2, icons[i].y - respValY(35), respValX(2000), respValY(1000)))

        if backIconRect in icons :
            pygame.draw.line(toolabarSurface, (51, 51, 51), (backIconRect.x + respValX(24), ty + respValY(26)), (backIconRect.x + respValX(11), ty + respValY(37)), 5)
            pygame.draw.line(toolabarSurface, (51, 51, 51), (backIconRect.x + respValX(24), ty + respValY(48)), (backIconRect.x + respValX(11), ty + respValY(37)), 5)
            pygame.draw.line(toolabarSurface, (51, 51, 51), (backIconRect.x + respValX(12), ty + respValY(37)), (backIconRect.x+respValX(43), ty + respValY(37)), 5)

        if createIconRect in icons :
            pygame.draw.line(toolabarSurface, (51, 51, 51), (createIconRect.x+respValX(12, False), ty + respValY(37, False)), (createIconRect.x+respValX(43, False), ty + respValY(37, False)), 5)
            pygame.draw.line(toolabarSurface, (51, 51, 51), (createIconRect.x+respValX(27.5, False), ty + respValY(22, False)), (createIconRect.x+respValX(27.5, False), ty + respValY(52, False)), 5)

        if deleteIconRect in icons :
            pygame.draw.rect(toolabarSurface, (51, 51, 51), (deleteIconRect.x+respValX(18), ty + respValY(30), respValX(20), respValY(25)), border_radius=respValX(3))
            pygame.draw.rect(toolabarSurface, (51, 51, 51), (deleteIconRect.x+respValX(12.5), ty + respValY(25), respValX(30), respValY(7)))
            pygame.draw.rect(toolabarSurface, (51, 51, 51), (deleteIconRect.x+respValX(17.5), ty + respValY(20), respValX(20), respValY(7)))
        
        if openIconRect in icons :
            folderRect = pygame.Rect(openIconRect.x+respValX(10), ty + respValY(30), respValX(35), respValY(20))
            pygame.draw.rect(toolabarSurface, (51, 51, 51), folderRect)
            pygame.draw.rect(toolabarSurface, (31, 31, 31), (folderRect.x, folderRect.y-5, respValX(20), respValY(10)))

        if undoIconRect in icons :
            pygame.draw.line(toolabarSurface, (51, 51, 51), (undoIconRect.x+respValX(22.5, False), ty + respValY(45, False)), (undoIconRect.x+respValX(43, False), ty + respValY(45, False)), 5)
            pygame.draw.line(toolabarSurface, (51, 51, 51), (undoIconRect.x+respValX(22.5, False), ty + respValY(30, False)), (undoIconRect.x+respValX(43, False), ty + respValY(30, False)), 5)
            pygame.draw.line(toolabarSurface, (51, 51, 51), (undoIconRect.x+respValX(43, False), ty + respValY(45, False)), (undoIconRect.x+respValX(43, False), ty + respValY(30, False)), 5)
            pygame.draw.polygon(toolabarSurface, (51, 51, 51), [(undoIconRect.x + respValX(22.5, False), ty + respValY(17.5 + 2.5, False)), (undoIconRect.x + respValX(22.5, False), ty + respValY(37.5 + 2.5, False)), (undoIconRect.x + respValX(10, False), ty + respValY(27.5 + 2.5, False))])
        
        if redoIconRect in icons :
            pygame.draw.line(toolabarSurface, (51, 51, 51), (redoIconRect.x+respValX(33, False), ty+respValY(45, False)), (redoIconRect.x+respValX(12.5, False), ty+respValY(45, False)), 5)
            pygame.draw.line(toolabarSurface, (51, 51, 51), (redoIconRect.x+respValX(33, False), ty+respValY(30, False)), (redoIconRect.x+respValX(12.5, False), ty+respValY(30, False)), 5)
            pygame.draw.line(toolabarSurface, (51, 51, 51), (redoIconRect.x+respValX(12.5, False), ty+respValY(45, False)), (redoIconRect.x+respValX(12.5, False), ty+respValY(30, False)), 5)
            pygame.draw.polygon(toolabarSurface, (51, 51, 51), [(redoIconRect.x+respValX(33, False), ty+respValY(20, False)), (redoIconRect.x+respValX(33, False), ty+respValY(40, False)), (redoIconRect.x+respValX(45.5, False), ty+respValY(30, False))])


        if enterQueryIconRect in icons :
            pygame.draw.line(toolabarSurface, (51, 51, 51), (enterQueryIconRect.x + respValX(18), ty + respValY(27)), (enterQueryIconRect.x + respValX(30), ty + respValY(36)), 5)
            pygame.draw.line(toolabarSurface, (51, 51, 51), (enterQueryIconRect.x + respValX(18), ty + respValY(45)), (enterQueryIconRect.x + respValX(30), ty + respValY(36)), 5)
            pygame.draw.line(toolabarSurface, (51, 51, 51), (enterQueryIconRect.x + respValX(30), ty + respValY(50)), (enterQueryIconRect.x + respValX(42), ty + respValY(50)), 5)

    if state == 0 :
        font = pygame.font.SysFont(mainFont,int(respValY(50,False)),bold=False)
        surface = font.render("DATABASE VIEW",True,(203, 206, 210))
        surface.set_alpha(200)
        screen.blit(surface, (respValX(30), respValY(25), respValX(2000), respValY(1000)))

    elif state == 1 :
        font = pygame.font.SysFont(mainFont,int(respValY(50,False)),bold=False)
        surface = font.render(f"{openedDatabase.name}",True,(203, 206, 210))
        surface.set_alpha(200)
        screen.blit(surface, (respValX(30), respValY(25), respValX(2000), respValY(1000)))

    screen.blit(vignette, (0, 0))

    if state == 2 :
        scrollValueVertical = max(0, scrollValueVertical)
        scrollValueHorizontal = max(0, scrollValueHorizontal)

        screen.fill((30,30,30))

        if not os.path.exists(os.path.join('DATABASES', "RESULT.csv")) :
            f = open(os.path.join('DATABASES', openedDatabase.name, f"{openedTable.name}.csv"), 'r', newline='')
        else :
            f = open(os.path.join('DATABASES', "RESULT.csv"), 'r', newline='')
        reader = csv.reader(f)
        all_data = [row for row in reader]
        f.close()
        header = all_data[0] if len(all_data)>0 else []

        visibleRows = 21
        visibleCols = 12
        rowStart = scrollValueVertical
        colStart = scrollValueHorizontal

        for screenRowIndex,j in enumerate(range(rowStart,rowStart+visibleRows)):
            pygame.draw.rect(screen,"BLACK",(respValX(10,False),respValY(55,False)+screenRowIndex*respValY(50,False),screen.get_width()-respValX(1880,False),respValY(40,False)), border_radius=respValX(5))
            font = pygame.font.SysFont(mainFont,int(respValY(40,False)),bold=False)
            text = str(j)
            surface = font.render(text,True,"WHITE")
            max_w = screen.get_width()-respValX(1880,False)
            if surface.get_width()>max_w: surface = pygame.transform.smoothscale(surface,(max_w,surface.get_height()))
            screen.blit(surface,(respValX(10,False)+respValX(10,False)*int(len(text)<2),respValY(57.5,False)+screenRowIndex*respValY(50,False)))

        for screenColIndex,i in enumerate(range(colStart,colStart+visibleCols)):
            pygame.draw.rect(screen,"BLACK",(respValX(55,False)+screenColIndex*respValX(170,False),respValY(10,False),respValX(160,False),respValY(40,False)), border_radius=respValX(5))
            font = pygame.font.SysFont(mainFont,int(respValY(40,False)),bold=False)
            text = header[i] if i<len(header) else ""
            surface = font.render(text,True,"WHITE")
            max_w = respValX(160,False)-respValX(20,False)
            if surface.get_width()>max_w: surface = pygame.transform.smoothscale(surface,(max_w,surface.get_height()))
            screen.blit(surface,(respValX(55,False)+screenColIndex*respValX(170,False)+respValX(10,False),respValY(12.5,False)))

        for screenColIndex,i in enumerate(range(colStart,colStart+visibleCols)):
            for screenRowIndex,j in enumerate(range(rowStart,rowStart+visibleRows)):
                pygame.draw.rect(screen,(200,200,200),(respValX(55,False)+screenColIndex*respValX(170,False),respValY(55,False)+screenRowIndex*respValY(50,False),respValX(160,False),respValY(40,False)), border_radius=respValX(5))
                if j+1<len(all_data) and i<len(all_data[j+1]):
                    text = all_data[j+1][i]
                    font = pygame.font.SysFont(mainFont,int(respValY(30,False)),bold=True)
                    surface = font.render(text,True,"BLACK")
                    max_w = respValX(160,False)-respValX(20,False)
                    if surface.get_width()>max_w: surface = pygame.transform.smoothscale(surface,(max_w,surface.get_height()))
                    screen.blit(surface,(respValX(55,False)+screenColIndex*respValX(170,False)+respValX(10,False),respValY(60,False)+screenRowIndex*respValY(50,False)))

    if state == 2 :
        screen.blit(gradient, (0,0))

    screen.blit(toolabarSurface, (0,0))

    pygame.display.flip()

    clock.tick(60)

pygame.quit()