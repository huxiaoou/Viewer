import datetime as dt
import pandas as pd
from rich.live import Live
from rich.table import Table
from tqsdk import TqApi, TqAuth
from husfort.qutility import SFG
from husfort.qinstruments import CInstrumentInfoTable


class CContract(object):
    def __init__(self, contract: str, instru_info_tab: CInstrumentInfoTable):
        self.__contract: str = contract
        self.__instrument: str = instru_info_tab.parse_instrument_from_contract(contract)
        self.__exchange: str = instru_info_tab.get_exchange_id(self.__instrument)
        self.__contract_multiplier: int = instru_info_tab.get_multiplier(self.__instrument)

    @property
    def contract(self) -> str:
        return self.__contract

    @property
    def multiplier(self) -> int:
        return self.__contract_multiplier

    @property
    def tq_id(self) -> str:
        return f"{self.__exchange}.{self.__contract}"

    def __gt__(self, other: "CContract"):
        return self.__contract > other.__contract

    def __repr__(self):
        return (f"Contract(contract={self.__contract}, "
                f"instrument={self.__instrument}, "
                f"exchange={self.__exchange}), "
                f"multiplier={self.__contract_multiplier})")


class CPosition(object):
    def __init__(self, contract: CContract, direction: int, qty: int, cost_price: float, base_price: float):
        self._contract = contract
        self._direction = direction
        self._qty = qty
        self._cost_price: float = cost_price
        self._base_price: float = base_price
        self._last_mkt_prc: float = base_price

    def __eq__(self, other: "CPosition"):
        return self.float_pnl_increment == other.float_pnl_increment

    def __gt__(self, other: "CPosition"):
        if self.float_pnl_increment > other.float_pnl_increment:
            return True
        elif self.float_pnl_increment < other.float_pnl_increment:
            return False
        else:
            if self.contract > other.contract:
                return True
            elif self.contract < other.contract:
                return False
            else:
                return self.direction > other.direction

    @property
    def contract(self) -> CContract:
        return self._contract

    @property
    def direction(self) -> int:
        return self._direction

    @property
    def qty(self) -> int:
        return self._qty

    @property
    def cost_price(self) -> float:
        return self._cost_price

    @property
    def base_price(self) -> float:
        return self._base_price

    @property
    def last_mkt_prc(self) -> float:
        return self._last_mkt_prc

    @last_mkt_prc.setter
    def last_mkt_prc(self, prc: float):
        if not pd.isna(prc):
            self._last_mkt_prc = prc

    @property
    def cost_val(self) -> float:
        return self._cost_price * self._qty * self._contract.multiplier * self._direction

    @property
    def base_val(self) -> float:
        return self._base_price * self._qty * self._contract.multiplier * self._direction

    @property
    def mkt_val(self) -> float:
        return self._last_mkt_prc * self._qty * self._contract.multiplier * self._direction

    @property
    def float_pnl(self) -> float:
        return self.mkt_val - self.cost_val

    @property
    def float_pnl_increment(self) -> float:
        return self.mkt_val - self.base_val


class CManagerViewer(object):
    def __init__(self, position_file_path: str, instru_info_tab: CInstrumentInfoTable):
        print(f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -     "
              f"INFO - loading data from {SFG(position_file_path)}")
        position_df = pd.read_csv(position_file_path)
        self.positions: list[CPosition] = []
        for _, r in position_df.iterrows():
            contract = CContract(contract=getattr(r, "contract"), instru_info_tab=instru_info_tab)
            self.positions.append(CPosition(
                contract=contract,
                direction=getattr(r, "direction"),
                qty=getattr(r, "qty"),
                cost_price=getattr(r, "aver_cost_price"),
                base_price=getattr(r, "last_market_price"),
            ))
        self.user_choice: str = ""
        self.pos_and_quotes_df = pd.DataFrame()

    @property
    def positions_size(self) -> int:
        return len(self.positions)

    def __generate_table(self):
        table = Table(title=f"\nPNL INCREMENT - {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}",
                      caption="[green]Press Ctrl + C to quit ...")
        table.add_column(header="CONTRACT", justify="right")
        table.add_column(header="DIR", justify="right")
        table.add_column(header="QTY", justify="right")
        table.add_column(header="COST", justify="right")
        table.add_column(header="BASE", justify="right")
        table.add_column(header="MKT", justify="right")
        table.add_column(header="COST", justify="right")
        table.add_column(header="BASE", justify="right")
        table.add_column(header="MKT", justify="right")
        table.add_column(header="FLOAT", justify="right")
        table.add_column(header="INCREMENT", justify="right")

        qty = 0
        cost_val, base_val, mkt_val = 0.0, 0.0, 0.0
        float_pnl, increment = 0.0, 0.0
        for pos in self.pos_and_quotes_df["pos"]:
            qty += pos.qty
            cost_val += pos.cost_val
            base_val += pos.base_val
            mkt_val += pos.mkt_val
            float_pnl += pos.float_pnl
            increment += pos.float_pnl_increment
            msg = (
                pos.contract.contract,
                str(pos.direction),
                str(pos.qty),
                f"{pos.cost_price:>10.2f}",
                f"{pos.base_price:>10.2f}",
                f"{pos.last_mkt_prc:>10.2f}",
                f"{pos.cost_val:>12.2f}",
                f"{pos.base_val:>12.2f}",
                f"{pos.mkt_val:>12.2f}",
                f"{pos.float_pnl:>10.2f}",
                f"{pos.float_pnl_increment:.2f}",
            )
            table.add_row(*msg)
        msg = (
            'SUM',
            '-',
            f"{qty:4d}",
            '-',
            '-',
            '-',
            f"{cost_val:.2f}",
            f"{base_val:.2f}",
            f"{mkt_val:.2f}",
            f"{float_pnl:.2f}",
            f"{increment:.2f}",
        )
        table.add_row(*msg)
        return table

    def create_quotes_df(self, tq_account: str, tq_password: str) -> TqApi:
        contracts = [pos.contract.tq_id for pos in self.positions]
        api = TqApi(auth=TqAuth(user_name=tq_account, password=tq_password))
        quotes = [api.get_quote(contract) for contract in contracts]
        self.pos_and_quotes_df = pd.DataFrame({"pos": self.positions, "quote": quotes})
        return api

    def update_from_quotes(self):
        for pos, quote in zip(self.pos_and_quotes_df["pos"], self.pos_and_quotes_df["quote"]):
            pos.last_mkt_prc = quote.last_price
        self.pos_and_quotes_df.sort_values(by="pos", ascending=False, inplace=True)
        return 0

    def main(self, tq_account: str, tq_password: str):
        api = self.create_quotes_df(tq_account, tq_password)
        try:
            with Live(self.__generate_table(), auto_refresh=False, screen=False) as live:
                while True:
                    api.wait_update()
                    self.update_from_quotes()
                    live.update(self.__generate_table(), refresh=True)
        except KeyboardInterrupt:
            print("\n", end="")
            api.close()
