-- Run on source SQL Server per replicated table (any technical person: fill table name only)
EXEC sys.sp_cdc_enable_db;
EXEC sys.sp_cdc_enable_table @source_schema=N'dbo', @source_name=N'so_mstr',
     @role_name=NULL, @supports_net_changes=1;
-- Lighter alternative when before-images not needed:
-- ALTER TABLE dbo.so_mstr ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
