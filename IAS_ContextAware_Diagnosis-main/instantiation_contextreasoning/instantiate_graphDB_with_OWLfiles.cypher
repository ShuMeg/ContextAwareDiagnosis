n10s_unique_uri ON (r:Resource) ASSERT r.uri IS UNIQUE;
CALL n10s.graphconfig.init();

CALL n10s.onto.import.fetch("file:///<<<PATH>>>>\\automated-wash-dryer-application.owl", "Turtle");
CALL n10s.onto.import.fetch("file:///<<<PATH>>>>\\wash-dry-system-top-ontology.owl", "Turtle");
CALL n10s.onto.import.fetch("file:///<<<PATH>>>>\\Thesis__\\Project\\final_use\\automated-wash-dryer-system-appliance-component-level.owl", "Turtle");
