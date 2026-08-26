import re
from pathlib import Path

from django.contrib.staticfiles import finders
from django.test import SimpleTestCase


class FrontendModuleTests(SimpleTestCase):
    def test_site_entrypoint_imports_existing_local_modules(self):
        entrypoint = Path(finders.find("movies/js/site.js"))
        source = entrypoint.read_text(encoding="utf-8")
        imports = re.findall(r'from "(\./[^"]+\.js)"', source)

        self.assertEqual(
            set(imports),
            {
                "./ai-filter.js",
                "./favorites.js",
                "./generator.js",
                "./history.js",
                "./motion.js",
                "./navigation.js",
                "./streaming.js",
            },
        )
        for module_path in imports:
            resolved_module = (entrypoint.parent / module_path).resolve()
            self.assertEqual(resolved_module.parent, entrypoint.parent.resolve())
            self.assertTrue(resolved_module.is_file(), module_path)

    def test_site_entrypoint_remains_only_an_initialisation_layer(self):
        entrypoint = Path(finders.find("movies/js/site.js"))

        self.assertLessEqual(
            len(entrypoint.read_text(encoding="utf-8").splitlines()), 25
        )
