import json
import uuid
from dataclasses import asdict
from types import MappingProxyType
from typing import Any

import pytest

import glab.comm.skills as skills
from glab.comm.library import LlmClient, AgentContext, Role, LlmMessage, LlmResponse, Skill
from tests.comm.test_settings import llm_ollama_gemma4, llm_ollama_ornith15

@pytest.fixture()
def llm(): return llm_ollama_gemma4()

@pytest.fixture()
def llm_ornith() -> LlmClient: return llm_ollama_ornith15()

def test_render_prompt_via_template_with_valid_template_name():
  """Test _render_prompt_via_template with valid template name"""
  prompt = skills._render_prompt_via_template(
    template="extract-address-info.md",
    user_input="Hello"
  )
  assert isinstance(prompt, str)
  assert prompt.index("Hello") > 0

def test_render_prompt_via_template_with_invalid_template_name():
  """Test _render_prompt_via_template with invalid template name"""
  prompt = skills._render_prompt_via_template(
    template="extract-address-info-xx.md",
    user_input="Hello"
  )
  assert isinstance(prompt, str)
  assert prompt == "Hello"

@pytest.mark.llm
@pytest.mark.ollama
def test_detect_language_skill_with_en(llm):
  data = "Duane Reipold, 360 Rainbow Blvd, Niagara Falls, NY 14303, United States"
  _detect_language_skill_with(llm, data, language="en")

@pytest.mark.llm
@pytest.mark.ollama
def test_detect_language_skill_with_zh(llm):
  data = "拉萨市城关区北京东路83号 西藏刚坚拉萨饭店营销部, 西藏自治区, 850000, 中国"
  _detect_language_skill_with(llm, data, language="zh")

def _detect_language_skill_with(llm, data: str, language: str):
  context = AgentContext(data, tool_registry=MappingProxyType({}), messages=[])
  prompt = skills.DetectLanguageSkill().instructions(context)
  assert prompt.index(data) > 0
  resp = _run_via_llm(llm, prompt)
  msg = resp.last_message(Role.ASSISTANT)
  assert isinstance(msg, LlmMessage)
  try: _json = json.loads(msg.content)
  except json.JSONDecodeError:
    assert pytest.fail(f"Failed to parse {msg.content} as JSON")
  assert _json["language"] == language
  assert _json["input"] == data

@pytest.mark.llm
@pytest.mark.ollama
def test_extract_address_info_skill_with_en_1(llm):
  data = "Duane Reipold, 360 Rainbow Blvd, Niagara Falls, NY 14303, United States"
  addr = _extract_address_info_skill_with(llm, "en", data)
  assert addr["name"] == "Duane Reipold"
  assert addr["country"] == "US"
  assert addr["province"] == "New York"
  assert addr["city"] == "Niagara Falls"
  assert addr["district"] is None
  assert addr["postal"] == "14303"
  assert addr["detail"] == "360 Rainbow Blvd"

@pytest.mark.llm
@pytest.mark.ollama
def test_extract_address_info_skill_with_en_2(llm):
  data = "1563 Springfield Ave, Maplewood, NJ 07040, United States, Fredrich Grasher"
  addr = _extract_address_info_skill_with(llm, "en", data)
  assert addr["name"] == "Fredrich Grasher"
  assert addr["country"] == "US"
  assert addr["province"] == "New Jersey"
  assert addr["city"] == "Maplewood"
  assert addr["district"] is None
  assert addr["postal"] == "07040"
  assert addr["detail"] == "1563 Springfield Ave"

@pytest.mark.llm
@pytest.mark.ollama
def test_extract_address_info_skill_with_en_3(llm):
  data = "US, CO 81401, Montrose, 1869 E Main St, Riichard Beliveau"
  addr = _extract_address_info_skill_with(llm, "en", data)
  assert addr["name"] == "Riichard Beliveau"
  assert addr["country"] == "US"
  assert addr["province"] == "Colorado"
  assert addr["city"] == "Montrose"
  assert addr["district"] is None
  assert addr["postal"] == "81401"
  assert addr["detail"] == "1869 E Main St"

@pytest.mark.llm
@pytest.mark.ollama
def test_extract_address_info_skill_with_zh_1(llm_ornith):
  data = "拉萨市城关区北京东路83号, 西藏刚坚拉萨饭店营销部, 西藏, 850000, 中国"
  addr = _extract_address_info_skill_with(llm_ornith, "zh", data)
  assert addr["name"] == "西藏刚坚拉萨饭店营销部"
  assert addr["country"] == "CN"
  assert addr["province"] == "西藏自治区"
  assert addr["city"] == "拉萨市"
  assert addr["district"] == "城关区"
  assert addr["postal"] == "850000"
  assert addr["detail"] == "北京东路83号"

@pytest.mark.llm
@pytest.mark.ollama
def test_extract_address_info_skill_with_zh_2(llm_ornith):
  data = "天津市河北区金纬路158号中国银行河北支行营业部, 天津市 300140, 表丽东"
  addr = _extract_address_info_skill_with(llm_ornith, "zh", data)
  assert addr["name"] == "表丽东"
  assert addr["country"] == "CN"
  assert addr["province"] == "天津市"
  assert addr["city"] == "天津市"
  assert addr["district"] == "河北区"
  assert addr["postal"] == "300140"
  assert addr["detail"] == "金纬路158号中国银行河北支行营业部"

@pytest.mark.llm
@pytest.mark.ollama
def test_extract_address_info_skill_with_zh_3(llm_ornith):
  data = "广东佛山市顺德区大门大岗头（即马岗大桥北）惠美庄食品有限公司3楼, 528300, 柘冬云"
  addr = _extract_address_info_skill_with(llm_ornith, "zh", data)
  assert addr["name"] == "柘冬云"
  assert addr["country"] == "CN"
  assert addr["province"] == "广东省"
  assert addr["city"] == "佛山市"
  assert addr["district"] == "顺德区"
  assert addr["postal"] == "528300"
  assert addr["detail"] == "大门大岗头（即马岗大桥北）惠美庄食品有限公司3楼"

def _extract_address_info_skill_with(llm: LlmClient, language: str, data: str) -> Any:
  query = """{{"language":"{language}", "input":"{user_input}"}}""".format(language=language, user_input=data)
  context = AgentContext(query, tool_registry=MappingProxyType({}), messages=[])
  prompt = skills.ExtractAddressInfoSkill().instructions(context)
  resp = _run_via_llm(llm, prompt)
  msg = resp.last_message(Role.ASSISTANT)
  assert isinstance(msg, LlmMessage)
  try: return json.loads(msg.content)
  except json.JSONDecodeError:
    assert pytest.fail(f"Failed to parse {msg.content} as JSON")

@pytest.mark.llm
@pytest.mark.ollama
def test_evaluate_address_data_skill_with_en_address(llm):
  data = """{"name": "Fredrich Grasher", "country": "US", "province": "New Jersey", "city": "Maplewood", "district": null, "postal": "07040", "detail": "1563 Springfield Ave"}"""
  rs = _evaluate_address_data_skill_with(llm, data)
  assert rs["valid"] == True
  assert rs["message"] is None
  assert rs["address"]["name"] == "Fredrich Grasher"
  assert rs["address"]["country"] == "US"
  assert rs["address"]["province"] == "New Jersey"
  assert rs["address"]["city"] == "Maplewood"
  assert rs["address"]["district"] is None
  assert rs["address"]["postal"] == "07040"
  assert rs["address"]["detail"] == "1563 Springfield Ave"

@pytest.mark.llm
@pytest.mark.ollama
def test_evaluate_address_data_skill_with_zh_address(llm):
  data = """{"name": "柘冬云", "country": "CN", "province": "广东省", "city": "佛山市", "district": "顺德区", "postal": "528300", "detail": "大门大岗头（即马岗大桥北）惠美庄食品有限公司3楼"}"""
  rs = _evaluate_address_data_skill_with(llm, data)
  assert rs["valid"] == True
  assert rs["message"] is None
  assert rs["address"]["name"] == "柘冬云"
  assert rs["address"]["country"] == "CN"
  assert rs["address"]["province"] == "广东省"
  assert rs["address"]["city"] == "佛山市"
  assert rs["address"]["district"] == "顺德区"
  assert rs["address"]["postal"] == "528300"
  assert rs["address"]["detail"] == "大门大岗头（即马岗大桥北）惠美庄食品有限公司3楼"

@pytest.mark.llm
@pytest.mark.ollama
def test_evaluate_address_data_skill_with_wrong_address_1(llm):
  data = """{"name": "Fredrich Grasher", "country": "United States", "province": "New York", "city": "Maplewood", "district": null, "postal": "07040", "detail": "1563 Springfield Ave"}"""
  rs = _evaluate_address_data_skill_with(llm, data)
  assert rs["valid"] == False
  assert rs["message"] == 'country must be ISO 3166-1 alpha-2 country code.'

@pytest.mark.llm
@pytest.mark.ollama
def test_evaluate_address_data_skill_with_wrong_address_2(llm):
  data = """{"name": "Fredrich Grasher", "country": "CN", "province": "New York", "city": "Maplewood", "district": null, "postal": "07040", "detail": "1563 Springfield Ave"}"""
  rs = _evaluate_address_data_skill_with(llm, data)
  assert rs["valid"] == False
  assert "inconsistent" in str(rs["message"])

def _evaluate_address_data_skill_with(llm: LlmClient, data: str) -> Any:
  context = AgentContext(data, tool_registry=MappingProxyType({}), messages=[])
  prompt = skills.EvaluateAddressDataSkill().instructions(context)
  resp = _run_via_llm(llm, prompt)
  msg = resp.last_message(Role.ASSISTANT)
  assert isinstance(msg, LlmMessage)
  try: return json.loads(msg.content)
  except json.JSONDecodeError:
    assert pytest.fail(f"Failed to parse {msg.content} as JSON")

@pytest.mark.llm
@pytest.mark.ollama
@pytest.mark.parametrize(
  "data, category",
  [
    pytest.param("""What problems does your product solve? Is it suitable for our use case?""", "pre-sale"),
    pytest.param("""What are your key advantages compared with similar products on the market?""", "pre-sale"),
    pytest.param("""What is included in the quote? What items are charged separately?""", "pre-sale"),
    pytest.param("""Is training included? Is it online or on-site training?""", "pre-sale"),
    pytest.param("""If we stop using the service later, can we export our data?""", "pre-sale"),

    pytest.param("""I haven’t received the order confirmation email. What should I do?""", "post-sale"),
    pytest.param("""My tracking hasn’t updated for several days. Is there any delay?""", "post-sale"),
    pytest.param("""How do I submit a return application? Do I need to get a return label?""", "post-sale"),
    pytest.param("""Where will the refund go? Original payment method or wallet balance?""", "post-sale"),
    pytest.param("""The item I received is damaged/wrong/defective. What can I do?""", "post-sale"),

    pytest.param("""What advertising channels and formats do you offer?""", "business"),
    pytest.param("""Do you offer reseller or distribution partnership programs?""", "business"),
    pytest.param("""Can we build product integrations between our platform and yours?""", "business"),
    pytest.param("""Do you have any minimum commitment requirements for partnership?""", "business"),
    pytest.param("""What is the process to start cooperation?""", "business"),

    pytest.param("""How are you?""", "unknown"),
    pytest.param("""What data is it today?""", "unknown"),
  ], ids = range(1,18)
)
def test_classify_customer_request(llm, data, category):
  _classify_customer_request(llm, data, category)

def _classify_customer_request(llm, data: str, category: str):
  context = AgentContext(data, tool_registry=MappingProxyType({}), messages=[])
  prompt = skills.ClassifyCustomerRequestSkill().instructions(context)
  resp = _run_via_llm(llm, prompt)
  msg = resp.last_message(Role.ASSISTANT)
  assert isinstance(msg, LlmMessage)
  try: _json = json.loads(msg.content)
  except json.JSONDecodeError:
    assert pytest.fail(f"Failed to parse {msg.content} as JSON")
  assert _json["category"] == category
  assert _json["input"] == data

@pytest.mark.llm
@pytest.mark.ollama
@pytest.mark.parametrize(
  "data",
  [
    pytest.param("""What problems does your product solve? Is it suitable for our use case?"""),
    pytest.param("""What are your key advantages compared with similar products on the market?"""),
    pytest.param("""What is included in the quote? What items are charged separately?"""),
    pytest.param("""Is training included? Is it online or on-site training?"""),
    pytest.param("""If we stop using the service later, can we export our data?"""),
  ], ids = range(1,6)
)
def test_generate_presale_support_reply(llm, data):
  _generate_customer_support_reply(llm, data, skills.SupportPreSaleSkill())

@pytest.mark.llm
@pytest.mark.ollama
@pytest.mark.parametrize(
  "data",
  [
    pytest.param("""I haven’t received the order confirmation email. What should I do?"""),
    pytest.param("""My tracking hasn’t updated for several days. Is there any delay?"""),
    pytest.param("""How do I submit a return application? Do I need to get a return label?"""),
    pytest.param("""Where will the refund go? Original payment method or wallet balance?"""),
    pytest.param("""The item I received is damaged/wrong/defective. What can I do?"""),
  ], ids = range(1,6)
)
def test_generate_postsale_support_reply(llm, data):
  _generate_customer_support_reply(llm, data, skills.SupportPostSaleSkill())

@pytest.mark.llm
@pytest.mark.ollama
@pytest.mark.parametrize(
  "data",
  [
    pytest.param("""What advertising channels and formats do you offer?"""),
    pytest.param("""Do you offer reseller or distribution partnership programs?"""),
    pytest.param("""Can we build product integrations between our platform and yours?"""),
    pytest.param("""Do you have any minimum commitment requirements for partnership?"""),
    pytest.param("""What is the process to start cooperation?"""),
  ], ids = range(1,6)
)
def test_generate_business_support_reply(llm, data):
  _generate_customer_support_reply(llm, data, skills.SupportBusinessCooperationSkill())

@pytest.mark.llm
@pytest.mark.ollama
@pytest.mark.parametrize(
  "data",
  [
    pytest.param("""How are you?"""),
    pytest.param("""What data is it today?"""),
  ], ids = range(1,3)
)
def test_generate_unknown_support_reply(llm, data):
  _generate_customer_support_reply(llm, data, skills.ForwardToHumanSupportSkill())

def _generate_customer_support_reply(llm, data: str, skill: Skill):
  context = AgentContext(data, tool_registry=MappingProxyType({}), messages=[])
  prompt = skill.instructions(context)
  resp = _run_via_llm(llm, prompt)
  msg = resp.last_message(Role.ASSISTANT)
  assert isinstance(msg, LlmMessage)
  try: _json = json.loads(msg.content)
  except json.JSONDecodeError:
    assert pytest.fail(f"Failed to parse {msg.content} as JSON")
  assert _json["reply"] is not None

def _run_via_llm(client: LlmClient, prompt: str) -> LlmResponse:
  msg = LlmMessage(Role.SYSTEM, prompt)
  resp = client.submit(str(uuid.uuid4()), [msg])
  print(json.dumps(asdict(resp), indent=2, ensure_ascii=False))
  assert len(resp.choices) == 1
  assert resp.choices[0].message.role == "assistant"
  assert isinstance(resp.choices[0].message.content, str)
  return resp