"""
pykis의 각종 유틸리티들을 모아둔 모듈
"""

# Copyright 2022 Jueon Park
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Callable
import pandas as pd
from .request_utility import Json, APIResponse


def get_currency_code_from_market_code(market_code: str) -> str:
    """
    거래소 코드를 입력 받아서 거래통화코드를 반환한다
    """
    market_code = market_code.upper()
    if market_code in ["NASD", "NAS", "NYSE", "AMEX", "AMS"]:
        return "USD"
    if market_code in ["SEHK", "HKS"]:
        return "HKD"
    if market_code in ["SHAA", "SZAA", "SHS", "SZS"]:
        return "CNY"
    if market_code in ["TKSE", "TSE"]:
        return "JPN"
    if market_code in ["HASE", "VNSE", "HSX", "HNX"]:
        return "VND"
    raise RuntimeError(f"invalid market code: {market_code}")


def get_continuous_query_code(is_kr: bool) -> str:
    """
    연속 querry 에 필요한 지역 관련 코드를 반환한다
    """
    return "100" if is_kr else "200"


def send_continuous_query(request_function: Callable[[Json, Json], APIResponse],
                          to_dataframe:
                          Callable[[APIResponse], pd.DataFrame],
                          is_kr: bool = True) -> pd.DataFrame:
    """
    조회 결과가 100건 이상 존재하는 경우 연속하여 query 후 전체 결과를 DataFrame으로 통합하여 반환한다.
    """
    max_count = 100
    outputs = []
    # 초기값
    extra_header = {}
    extra_param = {}
    for i in range(max_count):
        if i > 0:
            extra_header = {"tr_cont": "N"}    # 공백 : 초기 조회, N : 다음 데이터 조회
        res = request_function(
            extra_header=extra_header,
            extra_param=extra_param
        )
        output = to_dataframe(res)
        outputs.append(output)
        response_tr_cont = res.header["tr_cont"]
        no_more_data = response_tr_cont not in ["F", "M"]
        if no_more_data:
            break
        query_code = get_continuous_query_code(is_kr)
        extra_param[f"CTX_AREA_FK{query_code}"] = res.body[f"ctx_area_fk{query_code}"]
        extra_param[f"CTX_AREA_NK{query_code}"] = res.body[f"ctx_area_nk{query_code}"]
    return pd.concat(outputs)
