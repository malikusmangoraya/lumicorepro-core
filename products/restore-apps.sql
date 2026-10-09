-- Fix App.jsx for all 11 products: restore routes from lazy imports
-- Each product has unique lazy imports; we reconstruct routes from those

DO $$
DECLARE
  r RECORD;
  pkg TEXT;
  lines TEXT[];
  imports TEXT[];
  routes TEXT[];
  route_lines TEXT := '';
  product_name TEXT;
  staging TEXT;
BEGIN
  -- products that use MotionCanvas
  FOR r IN 
    SELECT 'apex' AS p UNION ALL SELECT 'aurelia-estates' UNION ALL SELECT 'aurum-fitness'
    UNION ALL SELECT 'claimflow-ai' UNION ALL SELECT 'flowpilot' UNION ALL SELECT 'meridian-capital'
    UNION ALL SELECT 'nuage-events' UNION ALL SELECT 'prestige-studio' UNION ALL SELECT 'resupro'
    UNION ALL SELECT 'saffron-voyage' UNION ALL SELECT 'studio-lumen'
  LOOP
    product_name := r.p;
    
    -- Read the file
    staging := 'products/' || product_name || '/frontend/src/App.jsx';
    pkg := pg_read_file(staging);
    IF pkg IS NULL THEN
      RAISE NOTICE 'Missing: %', staging;
      CONTINUE;
    END IF;
    
    lines := string_to_array(pkg, chr(13) || chr(10));
    
    -- Find all lazy imports: const X = lazy(() => import('./pages/X'));
    imports := ARRAY[]::TEXT[];
    FOR i IN 1..array_length(lines, 1) LOOP
      IF lines[i] ~* 'const \w+ = lazy\(\(\) => import\('.*/pages/(\w+)'\)\)' THEN
        imports := array_append(imports, lines[i]);
      END IF;
    END LOOP;
    
    IF array_length(imports, 1) IS NULL THEN
      RAISE NOTICE 'No lazy imports in %', product_name;
      CONTINUE;
    END IF;
    
    -- Map page names to route paths (convention-based)
    routes := ARRAY[]::TEXT[];
    FOR i IN 1..array_length(imports, 1) LOOP
      DECLARE
        comp_name TEXT;
        comp_path TEXT;
        route_path TEXT;
        import_line TEXT := imports[i];
        m TEXT[];
      BEGIN
        -- Extract component name: const X = lazy...
        comp_name := regexp_replace(import_line, 'const (\w+) = lazy\(\(\) => import\(.*\)', '\1');
        
        -- Extract page name from import path
        m := regexp_match(import_line, '\.\*/pages/(\w+)'\''\)');
        IF m[1] IS NOT NULL THEN
          comp_path := lower(m[1]);
          
          -- Build route path
          IF comp_path = 'home' THEN
            route_path := '/';
          ELSIF comp_path = 'about' OR comp_path = 'services' OR comp_path = 'pricing' 
                OR comp_path = 'contact' OR comp_path = 'privacy' OR comp_path = 'terms' THEN
            route_path := '/' || comp_path;
          ELSIF comp_path = 'login' THEN
            route_path := '/login';
          ELSIF comp_path = 'register' THEN
            route_path := '/register';
          ELSIF comp_path = 'account' THEN
            route_path := '/account';
          ELSIF comp_path = 'admin' THEN
            route_path := '/admin';
          ELSIF comp_path = 'listings' OR comp_path = 'programs' OR comp_path = 'portfolio'
                OR comp_path = 'events' OR comp_path = 'work' OR comp_path = 'templates'
                OR comp_path = 'itineraries' OR comp_path = 'galleries' OR comp_path = 'claims'
                OR comp_path = 'projects' THEN
            route_path := '/' || comp_path;
          ELSIF comp_path = 'checkout' THEN
            route_path := '/checkout';
          ELSE
            CONTINUE;
          END IF;
          
          -- Add route (skip home and catch-all for now)
          IF comp_path != 'home' THEN
            routes := array_append(routes, comp_path);
          END IF;
        END IF;
      END;
    END LOOP;
    
    -- Build the routes block
    route_lines := '';
    -- Home route first
    route_lines := route_lines || E'\n              <Route path="/" element={<Home />} />';
    -- Specific routes
    FOR i IN 1..array_length(routes, 1) LOOP
      route_lines := route_lines || E'\n              <Route path="/' || routes[i] || E'" element={<' || initcap(routes[i]) || ' />} />';
    END LOOP;
    -- Catch-all last
    route_lines := route_lines || E'\n              <Route path="*" element={<Home />} />';
    
    -- Read full content and replace routes block
    pkg := pg_read_file(staging);
    
    -- Find and replace the Routes block
    -- Pattern: <Routes> ... </Routes>
    pkg := regexp_replace(
      pkg,
      '<Routes>[\s\S]*?</Routes>',
      '<Routes>' || route_lines || E'\n            </Routes>',
      'g'
    );
    
    -- Also fix basename line
    pkg := regexp_replace(
      pkg,
      'const basename =.*?/<base>',
      'const basename = import.meta.env.BASE_URL || ''/'';',
      's'
    );
    
    -- Write back
    PERFORM pg_write_file(staging, pkg);
    
    RAISE NOTICE 'Fixed % (%d routes)', product_name, array_length(routes, 1) + 1;
  END LOOP;
END $$;
