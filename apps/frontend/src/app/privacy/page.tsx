export default function PrivacyPolicyPage() {
  return (
    <main className="mx-auto w-full max-w-4xl px-4 py-14">
      {/* Header */}
      <header className="mb-10 border-b border-slate-200 pb-6">
        <p className="text-xs uppercase tracking-[0.25em] text-slate-400">
          GoZip
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-800">
          개인정보처리방침
        </h1>
        <p className="mt-3 text-sm text-slate-500">
          본 개인정보처리방침은 GoZip(고집)(이하 “서비스”)가
          이용자의 개인정보를 어떻게 수집·이용·보호하는지를 설명합니다.
        </p>
      </header>

      {/* Content */}
      <section className="rounded-2xl border border-slate-200 bg-slate-50 px-6 py-10 text-sm leading-relaxed text-slate-600 shadow-sm">
        <div className="space-y-12">

          {/* 제1조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제1조 (수집하는 개인정보 항목)
            </h2>

            <p className="mt-3">
              서비스는 필수적인 범위 내에서 최소한의 정보만을 수집합니다.
            </p>

            <div className="mt-4 space-y-5">
              <div>
                <p className="font-semibold text-slate-800">
                  1. 이용자가 직접 제공하는 정보
                </p>
                <ul className="mt-2 list-disc space-y-2 pl-5">
                  <li>회원 식별 정보 (선택적): 닉네임 또는 사용자 식별값</li>
                  <li>찜한 매물 정보</li>
                  <li>매물 비교 기록</li>
                </ul>
              </div>

              <div>
                <p className="font-semibold text-slate-800">
                  2. 서비스 이용 과정에서 자동으로 수집되는 정보
                </p>
                <ul className="mt-2 list-disc space-y-2 pl-5">
                  <li>접속 로그 (IP 주소, 접속 시간, 접속 경로)</li>
                  <li>서비스 이용 기록 (페이지 조회, 매물 상세 조회 기록)</li>
                  <li>기기 정보 (브라우저 종류, 운영체제)</li>
                </ul>
              </div>

              <div>
                <p className="font-semibold text-slate-800">
                  3. 수집하지 않는 정보
                </p>

                <p className="mt-2">
                  서비스는 다음 정보를 수집하지 않습니다.
                </p>

                <ul className="mt-2 list-disc space-y-2 pl-5">
                  <li>주민등록번호, 계좌번호 등 민감한 개인정보</li>
                  <li>실제 계약 정보, 실명 인증 정보</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 제2조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제2조 (개인정보의 이용 목적)
            </h2>

            <p className="mt-3">
              수집된 개인정보는 다음 목적에 한하여 이용됩니다.
            </p>

            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>매물 찜·비교 기능 제공</li>
              <li>매물 조회 이력 기반 개인화 추천</li>
              <li>서비스 이용 통계 및 품질 개선</li>
              <li>서비스 오류 분석 및 안정성 확보</li>
            </ul>
          </div>

          {/* 제3조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제3조 (개인정보의 보관 및 이용 기간)
            </h2>

            <p className="mt-3">개인정보는 서비스 이용 기간 동안 보관됩니다.</p>

            <p className="mt-3">
              이용자가 서비스 이용을 중단하거나 삭제를 요청할 경우,
              <br />
              관련 정보는 지체 없이 파기됩니다.
            </p>

            <p className="mt-3">
              단, 관련 법령에 따라 보관이 필요한 경우 해당 기간 동안 보관할 수 있습니다.
            </p>
          </div>

          {/* 제4조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제4조 (개인정보의 제3자 제공)
            </h2>

            <p className="mt-3">
              서비스는 원칙적으로 이용자의 개인정보를 외부에 제공하지 않습니다.
              <br />
              다만, 다음의 경우는 예외로 합니다.
            </p>

            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>이용자의 사전 동의를 받은 경우</li>
              <li>법령에 따라 제공이 요구되는 경우</li>
            </ul>
          </div>

          {/* 제5조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제5조 (개인정보 보호를 위한 조치)
            </h2>

            <p className="mt-3">
              서비스는 개인정보 보호를 위해 다음과 같은 조치를 취합니다.
            </p>

            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>접근 권한 최소화</li>
              <li>내부 DB 접근 통제</li>
              <li>로그 기반 접근 기록 관리</li>
              <li>비식별화된 데이터 활용 원칙 준수</li>
            </ul>
          </div>

          {/* 제6조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제6조 (이용자의 권리)
            </h2>

            <p className="mt-3">
              이용자는 언제든지 다음 권리를 행사할 수 있습니다.
            </p>

            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>개인정보 열람 요청</li>
              <li>찜 목록·비교 기록 삭제 요청</li>
              <li>서비스 이용 중단 요청</li>
            </ul>
          </div>

        </div>
      </section>
    </main>
  );
}
