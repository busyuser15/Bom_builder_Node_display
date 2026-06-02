permissionset 50190 "Batch Permissions"
{
    Assignable = true;
    Caption = 'CKAPI_BOMBUILDER', MaxLength = 30;
    Permissions =
        table "BOM Entry Table" = X,
        tabledata "BOM Entry Table" = RMID;
}