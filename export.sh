docker exec sharinmod-db-1 pg_dump -U postgres -d sharinmod \
  --table=provider_models \
  --no-owner --no-acl \
  -f /tmp/sharinmod_vendor_tables.sql && \
docker cp sharinmod-db-1:/tmp/sharinmod_vendor_tables.sql ./sharinmod_vendor_tables.sql && \
echo "导出完成，文件大小：$(du -sh ./sharinmod_vendor_tables.sql | cut -f1)"
