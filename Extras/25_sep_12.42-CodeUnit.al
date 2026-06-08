codeunit 50182 "Codeunit Boms"
{
    var
        Present: dictionary of [text, List of [text]];
        HeaderToLine: Dictionary of [Text, integer];

    procedure initialiseUpdate()
    var
        BomEntry: record "BOM Entry Table";
        ParentNo: Text;
        BuffPar: list of [text];
        par: Text;
        BomHeader: record "Production BOM Header";
        BomLine: Record "Production BOM Line";
        ListOfLines: List of [text];
        holder: text;
        linenum: Integer;
    begin
        // Build unique parent list from staging table
        BuffPar.Clear();
        BomEntry.Reset();
        if BomEntry.FindSet() then
            repeat
                par := StrTrim(BomEntry.PARENT_PART_NUMBER);
                if par <> '' and not BuffPar.Contains(par) then begin
                    BuffPar.Add(par);
                end;
            until BomEntry.Next() = 0;

        // For each parent, scan existing Production BOM Lines and populate Present and HeaderToLine
        foreach ParentNo in BuffPar do begin
            if BomHeader.Get(ParentNo) then begin
                // collect all existing component numbers for this header
                ListOfLines := ListOf[Text]();
                BomLine.Reset();
                BomLine.SetRange("Production BOM No.", ParentNo);
                // track highest line number for next insertion
                linenum := 0;
                if BomLine.FindSet() then
                    repeat
                        ListOfLines.Add(BomLine."No.");
                        if BomLine."Line No." > linenum then
                            linenum := BomLine."Line No.";
                    until BomLine.Next() = 0;

                // store the next available line (highest found + 5) or default to 5
                if linenum = 0 then
                    HeaderToLine.Set(ParentNo, 5)
                else
                    HeaderToLine.Set(ParentNo, linenum + 5);

                if ListOfLines.Count() > 0 then
                    Present.Set(ParentNo, ListOfLines);
            end else begin
                // no header exists yet, initialize next line to 5
                HeaderToLine.Set(ParentNo, 5);
            end;
        end;
    end;

    procedure IsBomHeader(IgnoreSub: Boolean; type: text): Boolean
    var
        IsHeader: Boolean;

    begin
        if (format(IgnoreSub) = 'No') and (type = 'ASSEMBLY')
        then begin

            IsHeader := true;
        end
        else begin

            IsHeader := false;
        end;


        exit(IsHeader);
    end;

    procedure CreateHeader(CompNum: Text)
    var
        Item: Record Item;
        Headertable: Record "Production BOM Header";
        bomentry: Record "BOM Entry Table";
        linetable: Record "Production BOM Line";
        UnitOfMeasure: Record "Unit of Measure";
    begin
        Item.Reset();
        if Item.Get(CompNum) and bomentry.Get(CompNum) then begin
            HeaderTable.Init();
            HeaderTable."No." := CompNum;
            if StrLen(bomentry.Description) < 50 then begin
                Headertable."Search Name" := bomentry.Description;
                HeaderTable.Description := bomentry.Description;
            end else begin
                Headertable."Search Name" := CopyStr(bomentry.Description, 1, 49) + '*';
                HeaderTable.Description := CopyStr(bomentry.Description, 1, 49) + '*';
            end;
            Headertable."Unit of Measure Code" := 'TEST BC';

            HeaderTable.Insert();
            // persist production BOM number on the item
            if Item.Get(CompNum) then begin
                Item."Production BOM No." := HeaderTable."No.";
                Item.Modify();
            end;
        end;
    end;

    procedure CreateLine(CompNum: Text; ParentNum: Text; LineCounters: Dictionary of [Text, Integer])
    var
        Item: Record Item;
        Headertable: Record "Production BOM Header";
        bomentry: Record "BOM Entry Table";
        linetable: Record "Production BOM Line";
        UnitOfMeasure: Record "Unit of Measure";
        linenum: Integer;
        ListOfLines: list of [text];
        holder: text;
        Exists: Boolean;

    begin
        Item.Reset();

        if Item.Get(CompNum) and bomentry.Get(CompNum) and Headertable.Get(ParentNum) then begin
            // Determine next available Line No. for this header safely by finding the max existing
            linetable.Reset();
            linetable.SetRange("Production BOM No.", ParentNum);
            linenum := 0;
            if linetable.FindSet() then
                repeat
                    if linetable."Line No." > linenum then
                        linenum := linetable."Line No.";
                until linetable.Next() = 0;

            linenum := linenum + 5;

            if not DoesLineExist(CompNum, ParentNum) then begin
                linetable.Init();
                linetable."No." := CompNum;
                linetable."Production BOM No." := ParentNum;
                if StrLen(bomentry.Description) < 100 then
                    linetable.Description := bomentry.Description
                else
                    linetable.Description := CopyStr(bomentry.Description, 1, 99) + '*';

                linetable.Quantity := bomentry.QTY;
                linetable."Line No." := linenum;
                HeaderToLine.Set(ParentNum, linenum + 5);
                linetable.Insert();
            end else begin
                linetable.Reset();
                linetable.SetRange("No.", CompNum);
                linetable.SetRange("Production BOM No.", ParentNum);
                if linetable.FindFirst() then begin
                    linetable.Validate("Quantity per", bomentry.QTY);
                    linetable.Modify(true);
                    if Present.ContainsKey(ParentNum) then begin
                        ListOfLines := Present.Get(ParentNum);
                        ListOfLines.Remove(CompNum);
                        Present.Set(ParentNum, ListOfLines);
                    end;
                end;
            end;
        end;
    end;

    procedure DoesLineExist(CompNum: Text; LineNum: Integer; ProdBomNo: Text): Boolean

    var
        LineList: Record "Production BOM Line";
        LineExists: Boolean;
    begin
        LineList.Reset();
        LineList.SetRange("No.", CompNum);
        LineList.SetRange("Production BOM No.", ProdBomNo);
        if LineList.FindFirst() then
            LineExists := true
        else
            LineExists := false;
        exit(LineExists);
    end;

    procedure RemoveBOMLines()
    var
        BOMLine: Record "Production BOM Line";
        ComponentNo: Code[20];
        ParentNo: Code[20];
        ListOfComps: list of [text];
    begin
        foreach ParentNo in Present.Keys do begin
            ListOfComps := Present.Get(ParentNo);
            foreach ComponentNo in ListofComps do begin

                BOMLine.Reset();
                BOMLine.SetRange("Production BOM No.", ParentNo);
                BOMLine.SetRange("No.", ComponentNo);
                if BOMLine.FindSet() then
                    repeat
                        BOMLine.Delete();
                    until BOMLine.Next() = 0;
            end;
        end;
    end;

    procedure IsLevelZero(level: Integer): Boolean
    var
        Iszero: Boolean;
    begin
        if level = 0
        then
            Iszero := true
        else
            Iszero := false;

        exit(Iszero);
    end;

    procedure DoesHeaderExist(CompNum: Text): Boolean
    var
        HeaderList: Record "Production BOM Header";
        HeaderExists: Boolean;
        bomentry: record "BOM Entry Table";
    begin
        HeaderList.reset();
        HeaderList.SetRange("No.", CompNum);
        if HeaderList.FindFirst() then begin
            HeaderExists := true;
        end else begin
            HeaderExists := false
        end;
        exit(HeaderExists)
    end;

    Procedure DoesItemExist(CompNum: Text): Boolean
    var
        ItemList: Record "Item";
        ItemExists: Boolean;
    begin
        ItemList.reset();
        ItemList.SetRange("No.", CompNum);
        if ItemList.FindFirst() then begin
            ItemExists := true;
        end
        else begin
            ItemExists := false
        end;
        exit(ItemExists)
    end;

    procedure CreateItem(CompNum: code[20]; Desc: text)
    var
        ItemRec: Record "Item";
    begin
        ItemRec.Init();
        ItemRec."No." := CompNum;
        if StrLen(Desc) < 99 then begin
            ItemRec.Description := Desc;

        end
        else begin
            ItemRec.Description := (CopyStr(Desc, 1, 99) + '*');
        end;
        ItemRec.Insert();
    end;

    procedure ClearBOMEntryTable()
    var
        bomEntry: Record "BOM Entry Table";
    begin
        bomEntry.Reset(); // remove any filters
        if bomEntry.FindSet() then
            repeat
                bomEntry.Delete(true); // true = skip checks for triggers/permissions if needed
            until bomEntry.Next() = 0;
    end;

    procedure mainloop()
    var
        bomEntry: Record "BOM Entry Table";
        Items: Record "item";
        exists: Boolean;
        IsHeader: Boolean;
        currentline: Integer;
        LineCounters: Dictionary of [Text, Integer];
        CurrentLineNo: Integer;
        CurrentParent: Text;
    begin // #12
        initialiseUpdate();
        bomEntry.Reset();
        if bomEntry.FindSet() then
            repeat
                CurrentParent := bomEntry.PARENT_PART_NUMBER;
                if not LineCounters.ContainsKey(CurrentParent) then begin
                    LineCounters.Add(CurrentParent, 5)
                end;
            until bomEntry.Next() = 0;
        Message('beginging of code');
        //Item Check
        bomEntry.Reset();
        if bomEntry.FindSet() then
            repeat
                //message('comp part num:' + bomEntry.COMPONENT_PART_NUMBER + '\n', 'parent part num:' + bomEntry.PARENT_PART_NUMBER);
                exists := DoesItemExist(bomEntry.COMPONENT_PART_NUMBER);
                if exists = false then begin //#2
                    //Message('item should be created' + bomEntry.COMPONENT_PART_NUMBER);
                    CreateItem(bomEntry.COMPONENT_PART_NUMBER, bomEntry.Description);
                end; // #2
            until bomEntry.Next() = 0;

        message('past items');

        //BOM Header check
        bomEntry.Reset();
        if bomEntry.FindSet() then
            repeat
                //Message(bomentry.Description + ' description');
                //message('comp part num:' + bomEntry.COMPONENT_PART_NUMBER + '\n', 'parent part num:' + bomEntry.PARENT_PART_NUMBER);
                IsHeader := IsBomHeader(bomEntry.Treat_as_part, bomEntry.TYPE);
                if IsHeader = true then begin //#3
                    if DoesHeaderExist(bomEntry.COMPONENT_PART_NUMBER) = false then begin
                        //Message('UPDATED item should be created as a BOM header' + bomEntry.COMPONENT_PART_NUMBER);
                        CreateHeader(bomEntry.COMPONENT_PART_NUMBER);
                    end
                    else begin
                        items.get(bomEntry.COMPONENT_PART_NUMBER);
                        items."Production BOM No." := bomEntry.COMPONENT_PART_NUMBER
                    end;




                end
            until bomEntry.Next() = 0;


        bomEntry.Reset();
        if bomEntry.FindSet() then begin
            currentline := 0;
            repeat

                if IsLevelZero(bomentry.LEVEL) = false
                then begin
                    CreateLine(bomEntry.COMPONENT_PART_NUMBER, bomEntry.PARENT_PART_NUMBER, LineCounters);
                end;
            until bomEntry.Next() = 0;
        end;

        RemoveBOMLines()



    end;

}