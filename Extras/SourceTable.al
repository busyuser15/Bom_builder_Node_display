table 50180 "BOM Entry Table"
{
    DataClassification = ToBeClassified;

    fields
    {
        field(1; "LEVEL"; Integer)
        {
            DataClassification = ToBeClassified;
        }

        field(2; "PARENT_PART_NUMBER"; Text[250])
        {
            DataClassification = ToBeClassified;
        }

        field(3; "COMPONENT_PART_NUMBER"; Text[50])
        {
            DataClassification = ToBeClassified;
        }

        field(4; "STATUS"; Text[250])
        {
            DataClassification = ToBeClassified;
        }

        field(5; "TYPE"; Text[250])
        {
            DataClassification = ToBeClassified;
        }

        field(6; "QTY"; Decimal)
        {
            DataClassification = ToBeClassified;
        }

        field(7; "Attrib_SPAREPART"; Text[250])
        {
            DataClassification = ToBeClassified;
        }

        field(8; "Attrib_SPAREPART_SEVERITY"; Text[250])
        {
            DataClassification = ToBeClassified;
        }

        field(9; "Attrib_SPARESLISTQTY"; Decimal)
        {
            DataClassification = ToBeClassified;
        }

        field(10; "Phantom_Assembly"; Boolean)
        {
            DataClassification = ToBeClassified;
        }

        field(11; "Treat_as_part"; Boolean)
        {
            DataClassification = ToBeClassified;
        }

        field(12; "Description"; Text[250])
        {
            DataClassification = ToBeClassified;
        }
    }

    keys
    {
        key(PK; "COMPONENT_PART_NUMBER")
        {
            Clustered = true;
        }
    }

    trigger oninsert()
    var
        exists: Boolean;
        CodeUse: codeunit "Codeunit Boms";
    begin
        CodeUse.mainloop();
    end;
}
