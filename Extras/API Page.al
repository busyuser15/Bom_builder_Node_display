page 50181 "Breannan BOM API"
{
    PageType = API;
    SourceTable = "BOM Entry Table";
    APIPublisher = 'ck';
    APIGroup = 'integration';
    APIVersion = 'v2.0';
    EntityName = 'bomEntry';
    EntitySetName = 'bomEntries7';
    DelayedInsert = true;

    layout
    {
        area(content)
        {
            repeater(Group)
            {
                field("LEVEL"; Rec."LEVEL") { }
                field("PARENT_PART_NUMBER"; Rec."PARENT_PART_NUMBER") { }
                field("COMPONENT_PART_NUMBER"; Rec."COMPONENT_PART_NUMBER") { }
                field("STATUS"; Rec."STATUS") { }
                field("TYPE"; Rec."TYPE") { }
                field("QTY"; Rec."QTY") { }
                field("Attrib_SPAREPART"; Rec."Attrib_SPAREPART") { }
                field("Attrib_SPAREPART_SEVERITY"; Rec."Attrib_SPAREPART_SEVERITY") { }
                field("Attrib_SPARESLISTQTY"; Rec."Attrib_SPARESLISTQTY") { }
                field("Phantom_Assembly"; Rec."Phantom_Assembly") { }
                field("Treat_as_part"; Rec."Treat_as_part") { }
                field("Description"; Rec."Description") { }
            }

        }
    }

}
