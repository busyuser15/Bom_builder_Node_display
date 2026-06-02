page 50191 "BOM Import API"
{
    PageType = API;
    SourceTable = "BOM Dummy Load Table";
    APIPublisher = 'ck';
    APIGroup = 'integration';
    APIVersion = 'v1.0';
    EntityName = 'bomImport';
    EntitySetName = 'bomImports';
    delayedinsert = true;

    layout
    {
        area(content)
        {
            repeater(Group)
            {
                field("JsonPayload"; Rec.JsonPayload) { }
            }
        }
    }
}
