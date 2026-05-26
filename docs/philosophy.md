# DetoxBench Philosophy

DetoxBench는 LLM이 생성한 프로그램이 "정답 문자열"을 맞히는지가 아니라, 사용자의 행동에 따라 상태가 올바르게 변하는지를 평가한다.

## 핵심 원칙

1. 행동이 먼저다.
   평가는 실제 앱을 실행하고 버튼 클릭, 입력, 선택 같은 사용 행동을 수행한다.

2. 값보다 관계를 본다.
   카운터의 초기값이 무엇인지는 덜 중요하다. 증가 버튼을 누른 뒤 현재 값이 이전보다 1 커졌는지가 중요하다.

3. 상태는 투명해야 한다.
   평가 대상 앱은 평가 가능한 공개 상태를 제공해야 한다. 웹에서는 `window.__DETOX_STATE__` 같은 명시적 state probe를 사용한다.
   이 hook은 evaluator가 조작한 컴포넌트와 그 행동 결과를 식별할 수 있는 공개 관찰면이어야 한다. 레퍼런스 앱만의 내부 로그 형식이나 숨겨진 bookkeeping을 정답처럼 강제하기 위한 통로가 아니다.

4. 평가는 규칙 기반이다.
   evaluator는 AI가 아니다. DSL contract와 scenario를 컴파일한 selector, action, assertion 규칙만 실행한다.

5. 모든 행동은 증거를 남긴다.
   evaluator는 각 step마다 before/after 상태를 JSONL로 기록하고, before/after 화면을 screenshot으로 저장한다.

6. 레퍼런스 구현체는 benchmark의 일부다.
   좋은 benchmark는 DSL, 컴파일러, 평가기, 레퍼런스 앱이 서로 맞물려 함께 자란다. DetoxBench에서는 레퍼런스 구현체가 DSL contract와 scenario를 정확히 만족하는지 먼저 검증한 뒤 candidate를 평가한다.

7. Private test도 contract 밖으로 나가면 안 된다.
   숨길 수 있는 것은 테스트 순서와 구체 assertion이지, 새 요구사항 자체가 아니다. Contract에 없는 행동을 검사하는 scenario는 정식 점수가 아니라 contract gap을 찾기 위한 probe로 분류한다.

8. 구현 파일 구조는 평가 대상이 아니다.
   LLM이 만든 앱이 단일 HTML 파일이든 여러 JS/CSS 파일이든, 프레임워크 앱이든 상관없다. 평가기는 실행 가능한 URL, contract의 selector, 그리고 공개 state hook만 본다.

9. 성숙한 benchmark는 점수와 진단을 분리한다.
   Formal score는 contract로부터 도출 가능한 scoring scenario에서만 나온다. Contract gap, evaluator 설계 실험, reference-only behavior 확인은 probe로 남겨서 benchmark를 고치는 데 사용한다.

10. 평가기 자체도 측정 대상이다.
    DetoxBench의 산출물은 미리 준비된 앱 세트만이 아니다. Blind 구현체, known-bad 구현체, reference/independent 구현체를 반복 평가하면서 false positive와 false negative를 낮추는 방법론도 benchmark의 핵심 산출물이다.

## 왜 고정값 비교를 피하는가

LLM 생성 앱은 내부 seed, 초기 데이터, 렌더링 순서가 조금씩 다를 수 있다. 고정값만 비교하면 실제 행동은 맞는데 실패하거나, 반대로 하드코딩된 값으로 통과하는 앱이 생긴다.

DetoxBench는 다음과 같은 관계를 더 선호한다.

- A 행동 뒤 `counter.value`는 이전 snapshot보다 `+1`이어야 한다.
- 할 일을 추가하면 `todos.items` 길이는 이전보다 `+1`이어야 한다.
- 필터를 바꾸면 `visibleTexts`는 바뀔 수 있지만 `todos.items`는 그대로여야 한다.
- 테마 토글은 `ui.theme`만 바꾸고 업무 상태는 바꾸지 않아야 한다.
- 프로모션 적용 뒤 `checkout.total`은 이전보다 작아지고 `analytics.checkoutTotal`은 현재 `checkout.total`과 같아야 한다.

다만 관계형 평가가 "아무 값이나 허용한다"는 뜻은 아니다. 컴포넌트 id, selector, 가능한 action, 공개 state path, 상태 enum, 정책 이름, 파생 상태의 의미처럼 앱을 관찰하고 조작하는 데 필요한 표면은 contract에 명시되어야 한다. 실제 상품 가격, 카트 총액, ledger payload 같은 값은 contract가 요구한 경우에만 exact value로 채점한다.

## Contract와 Scenario의 경계

Contract는 candidate builder, 즉 LLM에게 공개되는 평가 표면이다. 현재 mainline에서는 `contract.dsl.yaml`이 그 역할을 한다. 여기에 컴포넌트, selector, 가능한 action, state schema, 그리고 반드시 지켜야 할 행동 제약을 적는다.

Scenario는 evaluator가 실행하는 절차다. 현재 mainline에서는 `scenarios.dsl.yaml`이 그 역할을 한다. Candidate 앱을 생성하는 LLM에게는 public/private 구분 없이 scenario 파일을 제공하지 않는다. Public 또는 development scenario라는 이름은 benchmark 작성자와 evaluator 검증을 위한 공개성일 뿐, candidate generation input이라는 뜻이 아니다.

Private scenario는 외부 평가에서 숨겨지는 scoring scenario다. 다만 private scenario도 contract에 이미 공개된 표면과 행동 제약만 사용할 수 있다.

사후에 scenario를 추가하는 것은 가능하다. 다만 새 scenario가 기존 contract로부터 도출 가능해야 한다. 그렇지 않다면 그 scenario는 candidate 실패가 아니라 contract gap을 발견한 것이다.

따라서 좋은 scenario는 "레퍼런스 구현체의 특정 숫자나 로그 모양"보다 "어떤 공개 컴포넌트 액션이 어떤 공개 상태 관계를 만들어야 하는가"를 적는다. Reference app과 blind candidate app이 내부 자료구조와 초기 세부값이 달라도 같은 contract 행동을 만족하면 통과할 수 있어야 한다.

## 성숙도

DetoxBench의 현재 목표는 단순히 scenario를 많이 만드는 것이 아니라, 각 scenario가 contract에 의해 정당화되고 실패가 해석 가능한 benchmark로 성장하는 것이다.

성숙도 기준과 현재 구현의 빈틈은 `docs/maturity.md`에 정리한다. 평가기를 안정화하는 반복 방법론은 `docs/evaluator-stabilization.md`에 정리한다. 공개/비공개 시나리오 분리, score weighting, model cohort, known-bad fixture 운영은 `docs/release-governance.md`에 정리한다. 새 target을 추가하거나 공개 평가로 올릴 때는 해당 문서들의 Level 2 이상 기준을 만족해야 한다. DSL 1.0 기준의 현재 한계와 다음 난이도 방향은 `docs/dsl-v100-analysis.md`와 `docs/gpt54-failure-frontier-claim-frontier.md`를 함께 본다. DSL 1.1 이후 2.0까지의 확장은 `docs/dsl-v110-analysis.md`, `docs/dsl-v120-analysis.md`, `docs/dsl-v200-analysis.md`, `docs/dsl-v2-roadmap.md`에 기록한다. DSL 3.0 capability train과 검증 기록은 `docs/dsl-v3-roadmap.md`에 정리한다. DSL 3.0 이후에도 아직 공정하게 표현할 수 없는 중요한 케이스는 `docs/dsl-v200-gap-analysis.md`를 기준으로 계속 갱신한다. 논문 작성 가능 범위와 아직 필요한 실험 증거는 `docs/paper-readiness.md`에 정리한다.
