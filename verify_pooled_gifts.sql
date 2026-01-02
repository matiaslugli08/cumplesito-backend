-- Verificar que la migración se ejecutó correctamente

-- 1. Verificar que las columnas existen
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'wishlist_items'
AND column_name IN ('item_type', 'target_amount', 'current_amount');

-- 2. Verificar que la tabla contributions existe
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_name = 'contributions'
);

-- 3. Actualizar items existentes para que tengan item_type = 'normal'
UPDATE wishlist_items
SET item_type = 'normal'
WHERE item_type IS NULL;

-- 4. Ver cuántos items hay de cada tipo
SELECT item_type, COUNT(*) as count
FROM wishlist_items
GROUP BY item_type;

COMMIT;
