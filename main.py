import argparse
from cls_positions import CManagerViewer, CInstrumentInfoTable

argument_parser = argparse.ArgumentParser(description="A viewer")
argument_parser.add_argument("--src", type=str, help="position file path")
args = argument_parser.parse_args()

# instru_info_tab_path = r"E:\Deploy\Data\Futures\InstrumentInfo3.csv"
instru_info_tab_path = r"E:\OneDrive\文档\Trading\Database\InstrumentInfo3.csv"
tq_account, tq_password = "15905194497", "Pkusms100871"
instru_info_tab = CInstrumentInfoTable(instru_info_tab_path, file_type="CSV")

mgr_viewer = CManagerViewer(position_file_path=args.src, instru_info_tab=instru_info_tab)
mgr_viewer.main(tq_account, tq_password)
