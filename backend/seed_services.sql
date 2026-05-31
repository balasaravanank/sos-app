-- Seed data for services_cache table
-- Chennai-based emergency services for fallback when Google Places API is unavailable

-- Hospitals
INSERT INTO services_cache (id, lat, lng, type, name, phone, address, rating, cached_at)
VALUES
  (gen_random_uuid(), 13.0615, 80.2519, 'hospital', 'Apollo Hospitals Greams Road', '+91-44-28290200', '21 Greams Ln, Chennai 600006', 4.3, NOW()),
  (gen_random_uuid(), 13.0067, 80.2206, 'hospital', 'MIOT International', '+91-44-42002288', '4/112 Mount Poonamallee Rd, Chennai 600089', 4.1, NOW()),
  (gen_random_uuid(), 13.0480, 80.2090, 'hospital', 'Fortis Malar Hospital', '+91-44-42892222', '52 1st Main Rd, Gandhi Nagar, Chennai 600020', 4.0, NOW()),
  (gen_random_uuid(), 13.0878, 80.2785, 'hospital', 'Government General Hospital', '+91-44-25305000', 'Park Town, Chennai 600003', 3.5, NOW()),
  (gen_random_uuid(), 13.1168, 80.1428, 'hospital', 'Sri Ramachandra Medical Centre', '+91-44-24768027', 'Porur, Chennai 600116', 4.2, NOW());

-- Police Stations
INSERT INTO services_cache (id, lat, lng, type, name, phone, address, rating, cached_at)
VALUES
  (gen_random_uuid(), 13.0827, 80.2707, 'police', 'Central Police Station', '100', 'Egmore, Chennai 600008', NULL, NOW()),
  (gen_random_uuid(), 13.0500, 80.2100, 'police', 'T. Nagar Police Station', '100', 'T. Nagar, Chennai 600017', NULL, NOW()),
  (gen_random_uuid(), 13.1200, 80.2800, 'police', 'Washermanpet Police Station', '100', 'Washermanpet, Chennai 600021', NULL, NOW()),
  (gen_random_uuid(), 13.0900, 80.2400, 'police', 'Nungambakkam Police Station', '100', 'Nungambakkam, Chennai 600034', NULL, NOW()),
  (gen_random_uuid(), 13.0600, 80.2600, 'police', 'Mylapore Police Station', '100', 'Mylapore, Chennai 600004', NULL, NOW());

-- Ambulance Services
INSERT INTO services_cache (id, lat, lng, type, name, phone, address, rating, cached_at)
VALUES
  (gen_random_uuid(), 13.0827, 80.2707, 'ambulance', 'GVK EMRI 108 Ambulance - Central', '108', 'Central Chennai', NULL, NOW()),
  (gen_random_uuid(), 13.0500, 80.2100, 'ambulance', 'GVK EMRI 108 Ambulance - South', '108', 'South Chennai', NULL, NOW()),
  (gen_random_uuid(), 13.1200, 80.2800, 'ambulance', 'GVK EMRI 108 Ambulance - North', '108', 'North Chennai', NULL, NOW()),
  (gen_random_uuid(), 13.0600, 80.2500, 'ambulance', 'Red Cross Ambulance Service', '+91-44-28254422', 'Red Cross Society, Chennai', 4.0, NOW()),
  (gen_random_uuid(), 13.0750, 80.2350, 'ambulance', 'Apollo Emergency Ambulance', '+91-44-28290200', 'Apollo Hospitals Network, Chennai', 4.5, NOW());

-- Towing Services
INSERT INTO services_cache (id, lat, lng, type, name, phone, address, rating, cached_at)
VALUES
  (gen_random_uuid(), 13.0700, 80.2400, 'towing', 'AAA Towing Services', '+91-98400-12345', 'Kodambakkam, Chennai 600024', 3.8, NOW()),
  (gen_random_uuid(), 13.0900, 80.2600, 'towing', 'Quick Tow Chennai', '+91-98410-67890', 'Purasawalkam, Chennai 600007', 3.5, NOW()),
  (gen_random_uuid(), 13.0450, 80.2350, 'towing', 'City Vehicle Recovery', '+91-99520-11223', 'Guindy, Chennai 600032', 3.9, NOW());

-- Puncture Shops
INSERT INTO services_cache (id, lat, lng, type, name, phone, address, rating, cached_at)
VALUES
  (gen_random_uuid(), 13.0800, 80.2650, 'puncture', 'Sri Ganesh Tyre Works', '+91-98765-43210', 'Egmore, Chennai 600008', 4.0, NOW()),
  (gen_random_uuid(), 13.0550, 80.2200, 'puncture', 'Kumar Puncture Shop', '+91-98765-11111', 'Ashok Nagar, Chennai 600083', 3.7, NOW());
