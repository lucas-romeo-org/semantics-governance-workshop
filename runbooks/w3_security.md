# Runbook · Wave 3 · RLS / CLS with ABAC

```bash
databricks bundle run w3_security -t <target> --profile <ws>
python scripts/show_verify.py --profile <ws> --job "sgw · w3 security"
```

## What gets created
- `governance.region_filter(region)`: leads and builders see every region · `wk_analysts_es` → ES · `wk_analysts_pt` → PT
- `governance.mask_pii(value)` → `****`
- Policy `region_rls` on schema `gold`: row filter on every column tagged `sgw_region_scope = region`
- Policy `pii_mask` on schema `gold`: column mask on every column tagged `sgw_pii`, except for `wk_pii_readers`
- `wk_security_admins` owns the functions and has `MANAGE` on `gold`, so it controls access without owning the data

## Verified result (sandbox)
```
✅ ana: regions ['ES']                    ✅ ana: PII masked
✅ pedro: regions ['PT']                  ✅ pedro: PII masked
✅ marta: regions ['ES','FR','IT','PT']   ✅ marta: PII clear
✅ new tagged table is filtered for Ana   (governance by tagging)
```
The verify step grants analysts `SELECT` on `gold` temporarily and revokes it at the end.

## Gotchas
- `DROP POLICY` has no `IF EXISTS`: check `SHOW POLICIES` first.
- Builders (`wk_data_engineers`) see every row, but PII stays masked for them too. Segregation of duties: building does not mean reading PII.
- ABAC requires serverless or DBR 16.4+. Unsupported compute fails closed.
