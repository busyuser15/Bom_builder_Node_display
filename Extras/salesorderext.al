pageextension 50190 "Sales Order Ext" extends "Order Planning"
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
        CodeUse.mainloop();
        //CodeUse.ClearBOMEntryTable();
        //bomEntry.Reset();
    end;
}
