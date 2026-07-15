"""Entry point for ``python -m chemauto``."""
import sys

if "--gui" in sys.argv:
    from chemauto.gui.log_browser import main
elif "--reference-search" in sys.argv:
    from chemauto.core.reference_search_launcher import launch_reference_search
    main = launch_reference_search
else:
    from chemauto.cli import main

if __name__ == "__main__":
    main()
