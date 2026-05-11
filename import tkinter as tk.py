import tkinter as tk
from tkinter import ttk
import openpyxl as op
import requests
import json
from tkinter import messagebox
from tkinter import filedialog
import uuid
import requests
import json
import webbrowser



#initialising
TruePartParent = []
HighlightOn = True
loaded = False
oldfilename = "holder, This is"
settingsOpen = False
global varCB
global activeClasses

#Initialising window
window = tk.Tk()
window.configure(bg="orange")  # Set background color
window.title("My Window")
levels =[]
window.geometry("1500x750")
window.grid_rowconfigure(0, weight=1)
window.grid_columnconfigure(0, weight=1)

#WIP CHECKBOX DATA
with open("ActiveWIP.txt", "r") as f:
    WIPActive = f.readlines()
if WIPActive[0]:
    varCB = tk.BooleanVar(value=True)
else:
    varCB = tk.BooleanVar(value=False)

#Folder Location data
global FolderLocation
with open("Folder_Location.txt", "r") as f:
    content = f.readlines()
location = content[0]

#Classifications to ignore data
def GetActives():
    activeClasses = []
    Classifications = {}
    with open("Classifications.txt", "r") as f:
        content = f.readlines()
        for line in content:
            SplitList = line.split(":")
            Classifications[SplitList[0]] = SplitList[1].strip("\n")
            if SplitList[1].strip("\n") == "True":
                activeClasses.append(SplitList[0])
    return activeClasses


# --- TOP HALF FRAME ---
HeaderFrame = tk.Frame(window, bg="black")
HeaderFrame.pack(side = "top",fill="x", padx=10, pady=10)
top_frame = tk.Frame(window, bg="orange")
top_frame.pack(side="top", fill="x", padx=10, pady=(0,10))

# Configure columns so things spread left/center/right
top_frame.grid_columnconfigure(0, weight=1)  # left
top_frame.grid_columnconfigure(1, weight=1)  # center
top_frame.grid_columnconfigure(2, weight=1)  # right

# LEFT: Editing frame
editing = tk.Frame(top_frame, bd=3, relief="solid")
editing.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
lbl = tk.Label(editing, text="PartNumber", font=("helvetica", 20))
lbl.pack(anchor="center", padx=10, pady=5)

Title = tk.Label(HeaderFrame, text= "CK International BOM to BC", font = ("helveticca Bold", 30),fg = "white", bg = "black")
Title.pack(anchor = "center", )

#Link to BC
def Go_BC():
    tasks_url = "https://businesscentral.dynamics.com/697d6604-5c29-4ca0-9dea-9db421a85492/CKIN01_UAT_131224?company=CK%20International%20Ltd&page=1171"
    webbrowser.open(tasks_url)

#Function to change phantom assembly to true or false
def ChangePhantom():
    PartNumEdit = lbl["text"]
    #take part number selected search through dictionary for part then chnage false to true or true to false
    ValueList = Comp_Values[PartNumEdit]
    Phantom = ValueList[3]
    if Phantom == False:
        Phantom = True
        #Keep a list of all changes
        PhantomChanges.append(PartNumEdit)
    else:
        Phantom = False
        try:
            #remove from changes if present 
            PhantomChanges.remove(PartNumEdit)
        finally:
            UpdateTree(IDStore, PartNumEdit)
    ValueList[3] = Phantom 
    Comp_Values[PartNumEdit] = ValueList
    UpdateTree(IDStore, PartNumEdit)

def ChangeSub():
    global SubChanges
    global IDStore
    PartNumEdit = lbl["text"]
    #take part number selected search through dictionary for part then chnage false to true or true to false
    ValueList = Comp_Values[PartNumEdit]
    Sub = ValueList[4]
    if Sub == False:
        Sub = True
        #keep track of all changes
        SubChanges.append(PartNumEdit)
    else:
        Sub = False

        remove = False
        for item4 in TruePartParent:
            if PartNumEdit == item4:
                remove = True
        if remove == True:
            #remove from changes if present
            TruePartParent.remove(PartNumEdit)
        try:
            SubChanges.remove(PartNumEdit)
        finally:
            ValueList[4] = Sub 
            Comp_Values[PartNumEdit] = ValueList
            UpdateTree(IDStore, PartNumEdit)
        
    ValueList[4] = Sub 
    Comp_Values[PartNumEdit] = ValueList
    UpdateTree(IDStore, PartNumEdit)

#This function gathers up information required for payload
def InfoCollect():
    
    Match = False
    for item in SubChanges:
        if item not in TruePartParent:
            #This list Contains Component Numbers for parts to ignore subassembly
            TruePartParent.append(item)
            
    msg = " Treat as part:\n" + "\n".join(TruePartParent) + "\n\n"
    msg += "Phantom Assembly:\n" + "\n".join(PhantomChanges)

    ans = messagebox.askquestion("askquestion", "This BOM will be uploaded to BC with the following changes:\n\n" + msg + "\nDo you wish to proceed?") 

    if ans == "no":
        return
    
    global AllData
    AllData = []
    global Component_level_lists
    global Parent_level_lists
    

    ExcelFileName = str(ExcelEntry.get())
    File_Path = location+ExcelFileName
    wb = op.load_workbook(File_Path)
    sheet = wb.active
    
    headersFULL = [cell.value for cell in sheet[1]]
    desired_headers = ["LEVEL", "PARENT PART NUMBER", "COMPONENT PART NUMBER",
                    "STATUS", "FILE TYPE", "QTY", "Attrib:SPAREPART", "Attrib:SPAREPART SEVERITY", "Attrib:SPARESLISTQTY"]
    
    headers = []
    indices = []


    for i, title in enumerate(headersFULL):
        if title in desired_headers:
            if title == "FILE TYPE":
                headers.append("TYPE")
            else:
                headers.append(title)
            indices.append(i)

    data = []

    #Moving through excel Sheet
    for row in sheet.iter_rows(min_row=2, values_only=True):
        row_dict = {}
        for j in range(len(headers)):
            value = row[indices[j]]
            if (headers[j] == "COMPONENT PART NUMBER" or headers[j] == "PARENT PART NUMBER") and value is not None:
                #Adding Revision versions to part numbers
                value = value.lstrip()
                value = value + Comp_rev[value]
            if headers[j] == "TYPE" and value is not None:
                if value[3:] == "ASM":
                    value = "ASSEMBLY"
                elif value[3:] == "PRT":
                    value = "PART"
            row_dict[headers[j]] = value

            

        # Add Phantom Assembly and Ignore Subassemblies and Description from Comp_Values
        comp_part = row_dict.get("COMPONENT PART NUMBER")
        if comp_part == "010012-01":
            print('match')
        if comp_part in Comp_Values:
            print('here ')
            values_list = Comp_Values[comp_part]
            row_dict["Phantom_Assembly"] = values_list[3]  # Phantom
            row_dict["Treat_as_part"] = values_list[4]  # Sub
            row_dict["Description"] = values_list[0] #description

        #Check Part number hasnt got a parent that has ignore sub assemblies
        for parentnum in TruePartParent:
            if parentnum is not None and row_dict["PARENT PART NUMBER"] is not None:
                #print(str(row_dict["PARENT PART NUMBER"]) + "   " + str(parentnum))
                if str(row_dict["PARENT PART NUMBER"]) ==  str(parentnum):
                    Match = True
        #if parent has ignore subassemblies
        if Match == True: 
            TruePartParent.append(row_dict["COMPONENT PART NUMBER"])
        else:            
            data.append(row_dict)
        Match = False
        
        #Renaming Fields to match the Names in Business Central
        row_dict["PARENT_PART_NUMBER"] = row_dict.pop("PARENT PART NUMBER", None)
        row_dict["COMPONENT_PART_NUMBER"] = row_dict.pop("COMPONENT PART NUMBER", None)
        row_dict["Attrib_SPAREPART"] = row_dict.pop("Attrib:SPAREPART", None)
        row_dict["Attrib_SPAREPART_SEVERITY"] = row_dict.pop("Attrib:SPAREPART SEVERITY", None)
        row_dict["Attrib_SPARESLISTQTY"] = row_dict.pop("Attrib:SPARESLISTQTY", None)
        if row_dict["COMPONENT_PART_NUMBER"] == '059112-00':
            print(row_dict)
    #Put into JSON format
    AllData = json.dumps(data, indent=2)
    #print(AllData)
    print('done infocollect')
    print(TruePartParent)
    return data

#This function sends the post request to the BC endpoint
def Post_Request():
    # Collect Payload data to send
    data = InfoCollect()

    # Credentials
    CLIENT_ID = "21e698d9-1eab-42be-beb7-76096e1af3db"
    CLIENT_SECRET = "waJ8Q~KQ5XQV0k7WFzXGyMmAjEy9XW_w6OhGWcdR"
    TENANT_ID = "697d6604-5c29-4ca0-9dea-9db421a85492"
    TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    token_data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://api.businesscentral.dynamics.com/.default"
    }

    # Send away for token
    token_resp = requests.post(TOKEN_URL, data=token_data)
    token_resp.raise_for_status()
    access_token = token_resp.json()["access_token"]

    # Headers for the *outer* batch request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": "odata.continue-on-error"
    }

    count = 0
    Max = len(data)

    while count < Max:
        payload = []  # reset each batch

        # iterate up to 99 items per batch
        for i in range(count, min(count + 99, Max)):
            lines = data[i]

            # make sure numeric fields are cast properly
            lines["LEVEL"] = int(lines["LEVEL"])
            lines["QTY"] = float(lines["QTY"])

            # build fresh dictionary for each request
            dictionary = {
                "method": "POST",
                "id": str(i + 1),  # unique ID per request in the batch
                "url": "companies(AED5BD5F-977B-ED11-9989-6045BD0CAE02)/bomEntries7",
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": lines
            }

            payload.append(dictionary)

        # wrap the subrequests into a batch
        itembody = {"requests": payload}

        # send the batch
        resp = requests.post(
            "https://api.businesscentral.dynamics.com/v2.0/697d6604-5c29-4ca0-9dea-9db421a85492/CKIN01_UAT_131224/api/ck/integration/v2.0/$batch",
            headers=headers,
            json=itembody
        )

        print("Batch response status:", resp.status_code)
        print(resp.text)  # debug which lines failed if any

        count += 99

    print("finished")

#This function handles Building the treeview
def BOM_layout():
    activeClasses = GetActives()
    global nextlevelparentsid
    global columns1
    global all_items
    global IDStore
    all_items = []
    #columns to be disaplyed in tree
    columns1 = ["Part Number", "Description", "Status", "Type","Phantom Assembly","Treat as part","Classification", "Attr:SpareParts", "Attr:SpareParts Qty", "Attr:SpareParts Severity"]
    
    global tree
    #Clear tree. This is used in case the function is called more than once
    for item in tree.get_children():
        tree.delete(item)
    
    #initalise columns in tree
    tree.heading("#0", text=columns1[0])
    tree.column("#0", width=20)
    tree.heading("#1", text=columns1[1])
    tree.column("#1", width=40)
    tree.heading("#2", text=columns1[2])
    tree.column("#2", width=10)
    tree.column("#2", anchor="center") 
    tree.heading("#3", text=columns1[3])
    tree.column("#3", width=10)
    tree.column("#3", anchor="center") 
    tree.heading("#4", text=columns1[4])
    tree.column("#4", width=10)
    tree.column("#4", anchor="center") 
    tree.heading("#5",text = columns1[5])
    tree.column("#5", width = 10)
    tree.column("#5", anchor="center") 
    tree.heading("#6",text = columns1[6])
    tree.column("#6", width = 40)
    tree.column("#6", anchor="center") 
    tree.heading("#7",text = columns1[7])
    tree.column("#7", width = 10)
    tree.column("#7", anchor="center") 
    tree.heading("#8",text = columns1[8])
    tree.column("#8", width = 10)
    tree.column("#8", anchor="center") 
    tree.heading("#9",text = columns1[9])
    tree.column("#9", width = 10)
    tree.column("#9", anchor="center") 
 

    tree.column("#0", anchor="w", stretch=True, minwidth=100, width=100)
    
    #Tags for tree. These are how to highlight certain items
    tree.tag_configure("red_highlight", background = "lightcoral", foreground = "white")
    tree.tag_configure("Normal", background = "white", foreground = "black")
    tree.tag_configure("Blue_Text", foreground="yellow", text = "bold", background = "black")
    #Binding the treeview to events like select and double click
    tree.bind("<<TreeviewSelect>>", on_select)
    tree.bind("<Double-1>", on_double_click)
    


    #LEVEL 0
    
    i =0
    CompPartsList = list(Comp_Status.keys())
    status = list(Comp_Status.values())
    is_red = False
    list2 = Component_level_lists[str(i)]
    if list2 != [None]:
        for j in range(len(list2)):
            PartNum = list2[j]
            
            y = 0
            for CompPart in CompPartsList: 
                CompPart = CompPart.lstrip()
                    
                y = y + 1
            Values = Comp_Values[PartNum]
            for actives in activeClasses:
                actives = actives.strip()
                classification_value = Values[5].strip()
                classification_value = classification_value.split(";")
                for Cls in classification_value:
                    if (Cls.lower()).strip().startswith(actives.lower().strip()):
                        TruePartParent.append(PartNum)
                        Values[4] = True
            node_id = tree.insert("", "end", text = PartNum, values= Values)
            IDStore = node_id
            all_items.append((node_id, ""))
            lbl.configure(text = PartNum)

    parent = PartNum
    parentid = node_id
    
    NextLevelParents = []
    nextlevelparentsid = []
    #Moving through each level
    for i in range(1,len(Component_level_lists)-1):
        if i>1:
            #searching thrpugh the above level for parents
            for k in range(len(NextLevelParents)):
                parent = NextLevelParents[k]
                parentid = nextlevelparentsid[k]
                list2 = Component_level_lists[str(i)]
                list3 = Parent_level_lists[str(i)]
                if list2 != [None]:
                    #moving through each part in current level and checking against parent
                    for j in range(len(list2)):
                        parentnum = list3[j].lstrip()
                        PartNum = list2[j].lstrip()
                        if parentnum == parent:
                            # just make the list once
                            CompPartsList = list(Comp_Status.keys())
                            status = list(Comp_Status.values())
                            # after loop, insert the node
                            Values = Comp_Values[PartNum]
                            val = Values[5]
                            if val is not None and val != "":
                                classification_value = str(val).strip()
                                print(classification_value + "\n")
                            else:
                                classification_value = ""
                            for actives in activeClasses:
                                actives = actives.strip()
                                if Values[5] is not None and Values[5] != "":
                                    classification_value = Values[5].strip()
                                    classification_value = classification_value.split(";")
                                else:
                                    classification_value = ""
                                    for Cls in classification_value:
                                        #print(Cls, "  ", actives)                                
                                        if (Cls.lower()).strip().startswith(actives.lower().strip()):
                                            TruePartParent.append(PartNum)
                                            Values[4] = True

                            node_id = tree.insert(parentid, "end", text=PartNum, values=Values)
                            all_items.append((node_id, parentid))
                            NextLevelParents.append(PartNum)
                            nextlevelparentsid.append(node_id)

        else:
                list2 = Component_level_lists[str(i)]
                list3 = Parent_level_lists[str(i)]                    
                for p in range(len(list3)):
                    parentnum = list3[p].lstrip()
                    PartNum = list2[p].lstrip()
                    
                    if parentnum == parent:
                        CompPartsList = list(Comp_Status.keys())
                        status = list(Comp_Status.values())
                        is_red = False
                        y = 0
                        # check if any CompPart matches PartNum
                        for CompPart in CompPartsList:                            
                            CompPart = CompPart.lstrip()
                            if CompPart == PartNum:

                                if status[y] == "WIP":
                                    is_red = True   
                            y = y + 1
                            # after loop, insert the node
                        Values = Comp_Values[PartNum]
                        classification_value = Values[5].strip()  # index 5 = "Classification"
                        for actives in activeClasses:
                            actives = actives.strip()
                            classification_value = Values[5].strip()
                            classification_value = classification_value.split(";")
                            for Cls in classification_value:
                                #print(Cls, "  ", actives)
                                if (Cls.lower()).strip().startswith(actives.lower().strip()):
                                    TruePartParent.append(PartNum)
                                    Values[4] = True
                        node_id = tree.insert(parentid, "end", text=PartNum, values=Values)
                        all_items.append((node_id, parentid))
                        NextLevelParents.append(PartNum)
                        nextlevelparentsid.append(node_id)
    ToggleRedFunc()
        


def dev():
    FileName = "061262 REV 0 MULTI LEVEL.xlsx"
    ExcelEntry.delete(0, tk.END)
    ExcelEntry.insert(0,FileName)
    GetText()

#DevLoad = tk.Button(window, text = "devload", command = dev)
#DevLoad.pack(anchor = "ne")


def autosize_columns(tree):
    for col in tree["columns"]:
        max_len = max(
            [len(str(tree.set(k, col))) for k in tree.get_children()] + [len(col)]
        )
        tree.column(col, width=max_len * 8)  # rough pixel estimate
        

#This function gets the data from the excel file
def GetText():

    global Component_level_lists
    global Parent_level_lists
    global Comp_Status
    global Comp_Values
    global PhantomChanges
    global SubChanges
    global loaded
    global oldfilename
    global TruePartParent
    global Parent_rev
    global Comp_rev

    #Initialise
    TruePartParent = []
    SubChanges = []
    PhantomChanges = []  
    #Grab Filename from entry box
    ExcelFileName = ExcelEntry.get()
    #concatonate with folder location
    File_Path = location+ExcelFileName
    try:
        #attempt to open excel
        wb = op.load_workbook(File_Path)
    except FileNotFoundError:
        tk.messagebox.showerror("Error", f"File not found:\n{File_Path}")
        return  
    except op.utils.exceptions.InvalidFileException:
        tk.messagebox.showerror("Error", f"Invalid file type:\n{File_Path}")
        return
    
    #if excel file has been previously loaded
    if loaded == True:
        if ExcelFileName == oldfilename:
            ans = messagebox.askquestion("askquestion", "Are you sure you want to reload this excel file\n" + str(File_Path)) 
        else:
            ans = messagebox.askquestion("askquestion", "Are you sure you want to load this new excel file\n" + "New file: " + str(File_Path) + "\nOld file: " + oldfilename)
        if ans == "no":
            return

    #variable to show excel file is currently loaded
    loaded = True
    #Current excel file
    sheet = wb.active

    #Dictionary for part number to revision to concatenate
    Comp_rev = {}
    for cell in sheet["F"]:
        CompPart = cell.value
        CompPart = CompPart.lstrip()
        rev = (sheet.cell(row=cell.row, column=cell.column + 1)).value
        try:
            num = float(rev)
            if num.is_integer():
                print("if", num)
                rev = "-0" + str(int(num))
            else:
                rev = "-" + str(num)[2:]
                print(num)
                print("else",str(rev))
        except:
            print("Input is not a number")
        Comp_rev[CompPart] = rev

    #Dictionary for parent part number to revision to concatenate
    Parent_rev = {}
    for cell in sheet["B"]:
        ParentPart = cell.value
        if ParentPart is not None:
            ParentPart = ParentPart.lstrip()
        rev = (sheet.cell(row=cell.row, column=cell.column + 1)).value
        try:
            num = float(rev)
            if num.is_integer():
                print("if", num)
                rev = "-0" + str(int(num))
            else:
                rev = "-" + str(num)[2:]
                print(num)
                print("else",str(rev))
        except :
            rev = "-00"
            print("Input is not a number")
        Parent_rev[ParentPart] = rev

    print(Comp_rev)
    print("\n", Parent_rev)

    #list for storing how many different levels there are
    levels =[]
    for cell in sheet["A"]:
        if cell.value is not None and cell.value not in levels:
            levels.append(cell.value)
    #dictionary for storing each component part number to its respective level
    Component_level_lists = {level: [] for level in levels}
    #dictionary for storing each parent part number to its respective level
    Parent_level_lists = {level: [] for level in levels}

    for cell in sheet["A"]:
        for level2 in Component_level_lists:
            list1 = Component_level_lists[level2]
            ParentPart = []
            Component_Part = []
            if cell.value == level2:
                Parent_cell = (sheet.cell(row=cell.row, column=cell.column + 1)).value
                if Parent_cell is not None:
                    Parent_cell = Parent_cell.lstrip()
                    Parent_cell = Parent_cell + Parent_rev[Parent_cell]
                Parent_level_lists[level2].append(Parent_cell)
        
                Component_cell = (sheet.cell(row=cell.row, column=cell.column + 5)).value
                Component_cell = Component_cell.lstrip()
                Component_cell = Component_cell + Comp_rev[Component_cell]
                Component_level_lists[level2].append(Component_cell)

    #build dictionary for component part number to respective status
    Comp_Status = {}
    for cell in sheet["F"]:
        CompPart = cell.value
        CompPart = CompPart.lstrip()
        CompPart = CompPart + Comp_rev[CompPart]
        Status = (sheet.cell(row=cell.row, column=cell.column + 4)).value
        Comp_Status[CompPart] = Status
    
    #build dictionary for component part to list of values needed for Treeview display
    Comp_Values = {}
    for cell in sheet["F"]:
        CompPart = cell.value
        #trim empty spaces before component part number
        CompPart = CompPart.lstrip()
        #concatenate with revision number
        CompPart = CompPart + Comp_rev[CompPart]
        type_ = (sheet.cell(row=cell.row, column=cell.column + 5)).value
        #trim first three characters off type "SLD"
        type_ = type_[3:]
        #change type to full name
        if type_ == "PRT":
            type_ = "Part"
        else:
            type_ = "Assembly"
        #initialise values list
        Values = []
        desc1 = sheet.cell(row=cell.row, column=cell.column + 6).value
        desc2 = sheet.cell(row=cell.row, column=cell.column + 7).value
        desc3 = sheet.cell(row=cell.row, column=cell.column + 8).value

        #pull in attribute fields
        AttrSparePart = sheet.cell(row=cell.row, column=cell.column + 38).value
        if AttrSparePart is None:
            AttrSparePart = ""
        AttrSparePartSeverity = sheet.cell(row=cell.row, column=cell.column + 39).value
        if AttrSparePartSeverity is None:
            AttrSparePartSeverity = ""
        AttrSparePartQty = sheet.cell(row=cell.row, column=cell.column + 40).value
        if AttrSparePartQty is None:
            AttrSparePartQty = ""

        #concatenate descriptions
        if desc2 is None:
            desc2 = ""
        if desc3 is None:
            desc3 = ""
        desc = str(desc1) + " " + str(desc2) + " " + str(desc3)
        Values.append(desc)
        Values.append(sheet.cell(row=cell.row, column=cell.column + 4).value)        
        Values.append(type_)
        Values.append(False) #treat as part
        Values.append(False) # phantom assembly
        Values.append(sheet.cell(row=cell.row, column=cell.column + 30).value)
        Values.append(AttrSparePart)
        Values.append(AttrSparePartSeverity)
        Values.append(AttrSparePartQty)

        #Store current component part number to its values in comp_vals dicitonary
        Comp_Values[CompPart] = Values
        #store filename currently loaded
        oldfilename = str(ExcelFileName)

    #begin to dispaly tree
    BOM_layout()
    autosize_columns(tree)

def AddEnd():
    ExcelEntry.insert(tk.END, " REV 0 MULTI LEVEL.xlsx")


phantombtn = tk.Button(editing, text="Phantom Assembly", font=("helvetica", 13), command=ChangePhantom)
phantombtn.pack(anchor="center", padx=10, pady=(5, 1))

ignoreSubAssembly = tk.Button(editing, text="Treat as part", font=("helvetica", 13), command=ChangeSub)
ignoreSubAssembly.pack(anchor="center", padx=10, pady=(0, 3))

# CENTER: File search
file_frame = tk.Frame(top_frame, bd=4, relief="solid")
file_frame.grid(row=0, column=1, sticky="n", padx=5, pady=5)

# Row 0: Label + Entry
lblInstruct = tk.Label(file_frame, text="File Name:", font=("helvetica", 15))
lblInstruct.grid(row=0, column=0, padx=5, pady=5, sticky="w")

ExcelEntry = tk.Entry(file_frame, width=40)
ExcelEntry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

# Row 1: Location (span both columns)
lblLocation = tk.Label(file_frame, text="Searching in: " + location)
lblLocation.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")

# Row 2: Buttons side by side
btn = tk.Button(file_frame, text="LOAD", background="darkgrey", command=GetText)
btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

MultilevelBtn = tk.Button(file_frame, text="...  REV 0 MULTI LEVEL.xlsx", command=AddEnd)
MultilevelBtn.grid(row=2, column=1, padx=5, pady=5, sticky="ew")


#Begin with search defaulted to by part
global Part
Part = True
def PartClick():
    #if seacrh by part is selcted
    global Part
    Part = True

def DescClick():
    #if search by description is selected
    global Part
    Part = False

def expand_all(parent=""):
    for item in tree.get_children(parent):
        tree.item(item, open=True)   # expand this node
        expand_all(item)


def PartSearch():
    #Reset previous search filter
    ResetSearch()
    global Part
    #grab what was seacrhed for
    SearchedFor = SearchEntry.get().lower()
    stack = list(tree.get_children(""))  # top-level items
    show_map = {}  # track which items should be visible

    all_items = []
    while stack:
        #removes last item from stack
        item_id = stack.pop()
        all_items.append(item_id)
        #adds chioldren of current item to stack
        stack.extend(tree.get_children(item_id))
    #searches from bottom up
    for item_id in reversed(all_items):
        if Part:  # search column 0 (Part Number)
            cell_text = tree.item(item_id, "text").lower()
        else:  # search column 1 (Description)
            cell_text = str(tree.item(item_id, "values")[0]).lower()
        #stores current CompPart
        Comppart = tree.item(item_id, "text").lower()
        #gathers the children of current comp part
        children = tree.get_children(item_id)

        #if the cell matches the entry then direct match = True
        direct_match = SearchedFor in cell_text
        #checks if cell has a child that matches
        child_match = any(show_map.get(c, False) for c in children)
        #if cell has a child that matches or its self matches then itemn should be shown
        show_item = direct_match or child_match
        #add ID and if it should be shown or not to map dictionary
        show_map[item_id] = show_item

        #Shows or doesnt show item
        if show_item:
            tree.reattach(item_id, tree.parent(item_id), "end")
        else:
            tree.detach(item_id)

        # Preserve all existing tags and add Blue_Text if needed
        if direct_match:
            current_tags = tree.item(item_id, "tags")
            # Convert to tuple if it’s a string or empty
            if isinstance(current_tags, str):
                current_tags = (current_tags,) if current_tags else ()
            # Convert to set for easy adding without duplicates
            tags_set = set(current_tags)
            tags_set.add("Blue_Text")
            tree.item(item_id, tags=tuple(tags_set))


def ResetSearch():
        global all_items
        #record expanded nodes
        expanded = set()
        #Make list "stack" of all top level nodes
        stack = list(tree.get_children(""))
        while stack:
            item = stack.pop()
            #check if node is currently expanded
            if tree.item(item, "open"):
                expanded.add(item)
            #adds the children of current item to the stack list
            stack.extend(tree.get_children(item))

        # reattach nodes in correct hierarchy
        for item_id, parent_id in all_items:
            tree.reattach(item_id, parent_id, "end")

            # remove Blue_Text tag but keep others
            current_tags = tree.item(item_id, "tags")
            if isinstance(current_tags, str):
                current_tags = (current_tags,) if current_tags else ()
            #These tags are set at the top of code
            tags_set = set(current_tags)
            tags_set.discard("Blue_Text")
            tree.item(item_id, tags=tuple(tags_set))

        # restore expanded state
        for item_id in expanded:
            tree.item(item_id, open=True)


    




# RIGHT: Search frame
Search = tk.Frame(top_frame, bd=3, relief="solid")
Search.grid(row=0, column=2, sticky="ne", padx=5, pady=5)

# Top label
rblbl = tk.Label(Search, text="Search by...")
rblbl.grid(row=0, column=0, columnspan=2, pady=(5,10))  # span both columns

# Shared variable for radio buttons
search_var = tk.StringVar(value="Part")
# Top label
rblbl = tk.Label(Search, text="Search by...")
rblbl.grid(row=0, column=0, columnspan=2, pady=(5,10))  # spans both columns

# Radio buttons in column 0
rbPart = tk.Radiobutton(Search, text="Part", variable=search_var, value="Part",command = PartClick)
rbDesc = tk.Radiobutton(Search, text="Description", variable=search_var, value="Description", command = DescClick)
rbPart.grid(row=1, column=0, sticky="w", padx=5)
rbDesc.grid(row=2, column=0, sticky="w", padx=5)

# Entry field in column 1, spanning rows 1–2
SearchEntry = tk.Entry(Search, width=20)
SearchEntry.grid(row=1, column=1, rowspan=2, sticky="w", padx=5)

# Buttons in row 3, side by side
Searchbtn = tk.Button(Search, text="Search", command=PartSearch)
Searchbtn.grid(row=3, column=0, pady=10, padx=5, sticky="ew")

ResetSearchbtn  = tk.Button(Search, text="Reset", command=ResetSearch)
ResetSearchbtn.grid(row=3, column=1, pady=10, padx=5, sticky="ew")


#function to update tree after changes
def UpdateTree(item_id, Target_part):
            UpdatedValues = Comp_Values[Target_part]
            tree.item(item_id, values=UpdatedValues)


#If description is double clicked
def on_double_click(event):
    global entry, col_index, item, row_id, cur_value

    #Only allow function to continue if a cell is double clicked
    region = tree.identify("region", event.x, event.y)
    if region != "cell":
        return
    
    row_id = tree.identify_row(event.y)
    column = tree.identify_column(event.x)

    #Only allow function to continue if description column is selected
    if column != "#1":
        return
    
    #Bbox gets exact coordinates and size
    x, y, width, height = tree.bbox(row_id, column)
    
    item = tree.item(row_id)
    col_index = int(column[1:]) - 1
    cur_value = item["values"][col_index]

    #create an entrybox the same size and on the same coordinates as cell
    entry = tk.Entry(tree)
    entry.place(x=x, y=y, width=width, height=height)
    #Iniialise entrybox with the current description
    entry.insert(0, cur_value)
    #Default the entrybox to be focused when created
    entry.focus()

    Comp_Values

    #When return button on keyboard is clicked or the entry box is clicked off of, run save edit function
    entry.bind("<Return>", save_edit)
    entry.bind("<FocusOut>", save_edit)


def save_edit(event=None):
    global entry, col_index, item, row_id, cur_value, Comp_Values
    #get new value
    new_val = entry.get()
    #update the compValue list
    values = list(item["values"])
    values[col_index] = new_val
    tree.item(row_id, values=values)

    # 2. get component part from column 0
    comp_part = tree.item(row_id, "text")  

    #update the compValue list
    ValuesList = Comp_Values[comp_part]
    ValuesList[0] = new_val
    Comp_Values[comp_part] = ValuesList
    

    # Destroy the entry after saving
    entry.destroy()

def on_select(event):
    global PartNumEdit
    global IDStore
    for item_id in tree.selection():
        IDStore = item_id
        #Selected Partnumber to edit
        PartNumEdit = tree.item(item_id, "text")
        #show on UI which was selected
        lbl.configure(text = PartNumEdit)

def Collapse_all(parent = ""):
    for item in tree.get_children(parent):
        tree.item(item, open=False)   # Collapse this node
        expand_all(item)

#if highlight wip is unselected
def set_all_tags(tree, tag="Normal"):
    #recurse function
    def recurse(items):
        for item in items:
            tree.item(item, tags=(tag,))
            #recurse through children
            recurse(tree.get_children(item))
    recurse(tree.get_children())


#if highlight wip is slected
def find_and_highlight(tree, parent="", part=""):
    for item_id in tree.get_children(parent):
        part = tree.item(item_id, "text")
        status = (Comp_Values[part])[1]
        if tree.item(item_id, "text") == part and status == "WIP":
            tree.item(item_id, tags=("red_highlight",))
        # recurse into children
        find_and_highlight(tree, item_id, part)

#If Highlight WIP is toggled
def ToggleRedFunc(parent = ""):
    global varCB
    #Get value from checkbox
    if varCB.get() == True:
        find_and_highlight(tree)        
    else:
        set_all_tags(tree, "Normal")



# ----------------------------
# BOM_Display Frame (bottom half)
# ----------------------------
BOM_Display = tk.Frame(window, bg="black")
BOM_Display.pack(fill="both", expand=True)

# Make two rows: row 0 = tree, row 1 = buttons
BOM_Display.grid_rowconfigure(0, weight=1)  # tree expands
BOM_Display.grid_rowconfigure(1, weight=0)  # buttons stay fixed

# Columns for buttons
for i in range(3):
    BOM_Display.grid_columnconfigure(i, weight=1)

# ----------------------------
# Inner frame for padding around tree
# ----------------------------
inner_frame = tk.Frame(BOM_Display, bg="pink")
inner_frame.grid(row=0, column=0, columnspan=3, sticky="nesw", padx=20, pady=20)

inner_frame.grid_rowconfigure(0, weight=1)
inner_frame.grid_columnconfigure(0, weight=1)

# ----------------------------
# Treeview
# ----------------------------
columns1 = ["Description", "Status", "Type","Phantom Assembly","Treat as part","Classification",
            "Attr:SpareParts", "Attr:SpareParts Qty", "Attr:SpareParts Severity"]

tree = ttk.Treeview(inner_frame, columns=columns1, show="tree headings")  # keep tree column for Part Number
tree.grid(row=0, column=0, sticky="nesw")

# Define headings
tree.heading("#0", text="Part Number")  # first column with hierarchy
tree.column("#0", width=150)  # adjust width for parts

for col in columns1:
    tree.heading(col, text=col)
    tree.column(col, width=120, anchor="center")  # adjust widths as needed

# ----------------------------
# Scrollbars
# ----------------------------
#add vertical scrollbar
vsb = ttk.Scrollbar(inner_frame, orient="vertical", command=tree.yview)
vsb.grid(row=0, column=1, sticky="ns")
tree.configure(yscrollcommand=vsb.set)

#hsb = ttk.Scrollbar(inner_frame, orient="horizontal", command=tree.xview)
#hsb.grid(row=1, column=0, columnspan=2, sticky="ew")
#tree.configure(xscrollcommand=hsb.set)

# ----------------------------
# Buttons
# ----------------------------
jsonBtn = tk.Button(BOM_Display, text="Upload", command=Post_Request, background=  "black")
expandbtn = tk.Button(BOM_Display, text="Expand all", command=expand_all, background=  "black")
collapsebtn = tk.Button(BOM_Display, text="Collapse all", command=Collapse_all, background=  "black")

jsonBtn.grid(row=2, column=0, padx=5, pady= 5)
expandbtn.grid(row=2, column=1, padx=5, pady=5)
collapsebtn.grid(row=2, column=2, padx=5, pady=5)


#dictionary to determine if classification is active, to check if treat as part should be defaulted to true or false
global Class_Active
Class_Active = {}

def select_folder():
    global folder_path
    folder_path = filedialog.askdirectory(title="Select Folder")
    folder_path = str(folder_path) + "/"
    if folder_path:
        FolderEntry.delete(0, tk.END)
        FolderEntry.insert(0, folder_path)
def Saving_Settings():
        ClassificationPreferences = {}
        all_iids = ClassTree.get_children()
        with open("Classifications.txt", "w") as f:
            for iid in all_iids:            
                value = ClassTree.set(iid, column="#1")
                ClassificationPreferences[value] = (checkboxes[iid])
                f.write(value.strip() + ":" + str(checkboxes[iid]).strip() + "\n")
        with open("ActiveWIP.txt", "w") as f:
            if varCB.get() == True:
                f.write("True")
            else:
                f.write("False")
        with open("Folder_Location.txt","w") as f:
            f.write(FolderEntry.get())

def CloseSettings():
    global location
    Saving_Settings()
    folder_path = FolderEntry.get()
    location = folder_path
    lblLocation.configure(text = location)
    Settings.place_forget()
    window.update_idletasks()
    window.update()



def OpenSettings():
    #api()
    global settingsOpen
    if settingsOpen:
        Settings.place(x = 0, y = 0)
    else:
        CreateSettings()

global checkboxes
checkboxes = {}

def CreateNewClassification():
    global blank
    blank = False
    iid = str(uuid.uuid4())
    ClassTree.insert("", "end", iid=iid, values=("", "☑"))
    
    # make sure checkboxes is a dict
    checkboxes[iid] = True
    
    # open the entry to edit the first column (#1)
    edit_item(iid, column="#1")



def edit_item(iid, column="#1"):
    bbox = ClassTree.bbox(iid, column)
    if not bbox:
        return 
    x, y, width, height = bbox

    value = ClassTree.set(iid, column=column)

    entry = tk.Entry(ClassTree)
    entry.insert(0, value)
    entry.focus()
    entry.place(x=x, y=y, width=width, height=height)

    def save_edit(event=None):
        new_value = entry.get().strip()
        if new_value == "":
            ClassTree.delete(iid)
            if iid in checkboxes:
                del checkboxes[iid]
        else:
            ClassTree.set(iid, column=column, value=new_value)
        entry.destroy()
        Class_Active[value] = checkboxes[iid]

    entry.bind("<Return>", save_edit)
    entry.bind("<FocusOut>", save_edit)


def toggle_checkbox(event):
    item = ClassTree.identify_row(event.y)
    column = ClassTree.identify_column(event.x)

    if not item:
        return

    if column == "#2":
        current = checkboxes[item]
        new_state = not current
        checkboxes[item] = new_state
        ClassTree.set(item, column="#2", value="☑" if new_state else "☐")

def DeleteClassification():
    selected = ClassTree.selection()
    for iid in selected:
        if iid in checkboxes:
            del checkboxes[iid]
        ClassTree.delete(iid)

def CreateSettings():
    global settingsOpen
    global Settings
    global FolderEntry
    global ClassTree  
    global classificationFrame
    global checkboxes
    global varCB
    global FolderLocation

    checkboxes = {}
    settingsOpen = True
    Settings = tk.Frame(window, bg="grey", width=750, height=500)
    Settings.place(x=0, y=0)
    Settings.lift()
    Settings.pack_propagate(False)

    # Title
    settingslbl = tk.Label(Settings, text="SETTINGS", font=("Helvetica", 20),bd=4, relief ="solid")
    settingslbl.grid(row=0, column=0, columnspan=3, pady=10)

    # --- Folder Selection Frame ---
    FileFrame = tk.Frame(Settings, bg="grey",bd=2, relief ="solid")
    FileFrame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
    FileFrame.grid_columnconfigure(1, weight=1)

    folderlbl = tk.Label(FileFrame, text="Folder Location:", bg="grey")
    folderlbl.grid(row=0, column=0, sticky="w", padx=5, pady=5)

    FolderEntry = tk.Entry(FileFrame)
    FolderEntry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
    FolderEntry.insert(0, location)

    select_btn = tk.Button(FileFrame, text="Browse", command=select_folder)
    select_btn.grid(row=0, column=2, padx=5, pady=5)

    # --- Classification Frame ---
    classificationFrame = tk.Frame(Settings, bg="grey", width=750, height=230,bd=2, relief ="solid")
    classificationFrame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
    classificationFrame.grid_propagate(False)

    ClassificationLbl = tk.Label(
        classificationFrame,
        text="Select which Classifications \nto treat as parts by default", background = "grey"
    )
    ClassificationLbl.grid(row=1, column=0, pady=5, padx=5, sticky="w")

    ClassTree = ttk.Treeview(
        classificationFrame,
        columns=("Classification", "Treat as Part"),
        show="headings",
        height=8
    )

    ClassTree.heading("Classification", text="Classification")
    ClassTree.heading("Treat as Part", text="Treat as Part")
    ClassTree.column("Classification", width=250, anchor="w")
    ClassTree.column("Treat as Part", width=80, anchor="center")
    ClassTree.grid(row=1, column=1, padx=5, pady=15, sticky="nsew")
    ClassTree.bind("<Button-1>", toggle_checkbox)


    def edit_cell(event):
        rowid = ClassTree.identify_row(event.y)
        col = ClassTree.identify_column(event.x)
        if col != "#1" or not rowid:  
            return


        x, y, w, h = ClassTree.bbox(rowid, "Classification")


        old_value = ClassTree.set(rowid, "Classification")


        entry = tk.Entry(ClassTree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, old_value)
        entry.focus()

        def save_edit(event=None):
            new_value = entry.get().strip()
            if new_value:
                ClassTree.set(rowid, "Classification", new_value)
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)

    ClassTree.bind("<Double-1>", edit_cell)


    ClassButtons = tk.Frame(classificationFrame, bg="grey")
    ClassButtons.grid(row=1, column=2, padx=5, pady=5, sticky="e")

    def GetSettingsData ():
        #Classification Data#
        Classifications = {}
        with open("Classifications.txt", "r") as f:  # "r" = read mode
            content = f.readlines()
            for line in content:
                SplitList = line.split(":")
                Classifications[SplitList[0]] = SplitList[1].strip("\n")

        Strings = Classifications.keys()
        for strings in Strings:
            iid = str(uuid.uuid4())
            ticked = (Classifications[strings])
            if ticked == "True":
                box = "☑" 
                checkboxes[iid] = True
            else:                
                box = "☐"
                checkboxes[iid] = False
            values = [strings,box]
            ClassTree.insert("", "end",iid =iid, values=values)

    Newbtn = tk.Button(ClassButtons, text="New", command=CreateNewClassification)
    Newbtn.grid(row=0, column=0, pady=2)
    Deletebtn = tk.Button(ClassButtons, text="Delete", command=DeleteClassification)
    Deletebtn.grid(row=1, column=0, pady=2)

    # --- WIP Frame ---
    WipFrame = tk.Frame(Settings, bg="grey",bd=2, relief ="solid")
    WipFrame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

    cb = tk.Checkbutton(WipFrame, text="Highlight WIP", variable=varCB, command=ToggleRedFunc, background = "grey")
    cb.select()
    cb.pack(anchor="sw")


    CloseSettingsbtn = tk.Button(Settings, text="Save and Exit", command=CloseSettings, background = "grey")
    CloseSettingsbtn.grid(row=3, column=2, sticky="e", padx=10, pady=10)

    GetSettingsData()


settingsbtn = tk.Button(BOM_Display,text = "Settings", background=  "black", command = OpenSettings)
settingsbtn.grid(row=3, column=1, padx = 5, pady = 5)

window.mainloop()