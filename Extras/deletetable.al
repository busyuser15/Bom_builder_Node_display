pageextension 50191 "delete table ext" extends "Item Tracing"
{
    actions
    {
        // You can add actions if needed
    }

    trigger OnOpenPage();
    var
        exists: Boolean;
        CodeUse: codeunit "Codeunit Boms";
        bomEntry: record "BOM Entry Table";
    begin
        CodeUse.ClearBOMEntryTable();
        bomEntry.Reset();
    end;
}
