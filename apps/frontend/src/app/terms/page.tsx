export default function TermsPage() {
  return (
    <main className="mx-auto w-full max-w-4xl px-4 py-14">
      {/* Header */}
      <header className="mb-10 border-b border-slate-200 pb-6">
        <p className="text-xs uppercase tracking-[0.25em] text-slate-400">
          GoZip
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-800">
          이용약관
        </h1>
        <p className="mt-3 text-sm text-slate-500">
          본 약관은 GoZip 서비스 이용과 관련된 기본 사항을 안내합니다.
        </p>
      </header>

      {/* Content */}
      <section className="rounded-2xl border border-slate-200 bg-slate-50 px-6 py-10 text-sm leading-relaxed text-slate-600 shadow-sm">
        <div className="space-y-12">

          {/* 제1조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제1조 (목적)
            </h2>
            <p className="mt-2">
              본 약관은 GoZip(고집)(이하 “서비스”)가 제공하는 AI 기반 부동산 정보 분석 및 추천
              서비스의 이용과 관련하여 서비스 제공자와 이용자 간의 권리·의무 및 책임사항을
              규정함을 목적으로 합니다.
            </p>
          </div>

          {/* 제2조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제2조 (정의)
            </h2>
            <div className="mt-3 space-y-4">
              <p>본 약관에서 사용하는 용어의 정의는 다음과 같습니다.</p>

              <div>
                <p className="font-semibold text-slate-800">서비스란</p>
                <p>
                  부동산 매물 정보, 실거래 데이터, 금융·거시경제 지표 등을 기반으로 AI 모델을 통해
                  매물 분석, 비교, 추천, 지표(온도 시스템 등)를 제공하는 온라인 서비스를 말합니다.
                </p>
              </div>

              <div>
                <p className="font-semibold text-slate-800">이용자란</p>
                <p>본 약관에 동의하고 서비스를 이용하는 모든 회원 및 비회원을 말합니다.</p>
              </div>

              <div>
                <p className="font-semibold text-slate-800">콘텐츠란</p>
                <p>
                  서비스에서 제공되는 매물 정보, 분석 결과, 지표, 그래프, 설명 텍스트, 추천 결과 등
                  일체의 정보를 말합니다.
                </p>
              </div>

              <div>
                <p className="font-semibold text-slate-800">AI 분석 결과란</p>
                <p>
                  머신러닝·딥러닝 모델을 통해 산출된 예측값, 구간 분류, 비교 결과 등을 의미합니다.
                </p>
              </div>
            </div>
          </div>

          {/* 제3조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제3조 (약관의 효력 및 변경)
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>본 약관은 서비스 화면에 게시하거나 기타 방법으로 이용자에게 공지함으로써 효력이 발생합니다.</li>
              <li>
                서비스는 관련 법령을 위반하지 않는 범위에서 약관을 변경할 수 있으며, 변경 시 적용일자 및
                변경 사유를 명시하여 사전에 공지합니다.
              </li>
              <li>이용자가 변경된 약관에 동의하지 않을 경우 서비스 이용을 중단할 수 있습니다.</li>
            </ul>
          </div>

          {/* 제4조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제4조 (서비스의 제공 내용)
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>부동산 매물 정보 조회 및 상세 정보 제공</li>
              <li>실거래 데이터 및 통계 기반 매물 분석</li>
              <li>AI 모델을 활용한 가격 수준 판단(저렴·적정·비쌈 등 구간화)</li>
              <li>생활편의, 교통, 안전, 환경 등 지표 기반 매물 평가(온도 시스템)</li>
              <li>매물 비교, 추천 및 참고용 분석 정보 제공</li>
              <li>기타 서비스가 추가로 제공하는 부가 기능</li>
            </ul>
            <p className="mt-3 text-xs text-slate-500">
              ※ 서비스 내용은 운영 정책 및 기술적 환경에 따라 변경될 수 있습니다.
            </p>
          </div>

          {/* 제5조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제5조 (서비스 이용의 한계 및 고지)
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>본 서비스에서 제공하는 모든 정보와 AI 분석 결과는 참고용 정보이며, 실제 거래 가격, 계약 조건, 투자 수익을 보장하지 않습니다.</li>
              <li>서비스의 분석 결과는 데이터 수집 시점, 모델 구조, 통계적 추정에 따라 오차가 발생할 수 있습니다.</li>
              <li>이용자는 서비스의 정보를 최종 의사결정의 단독 근거로 사용해서는 안 되며, 실제 부동산 거래 시에는 공인중개사 또는 전문가 상담을 병행해야 합니다.</li>
            </ul>
          </div>

          {/* 제6조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제6조 (이용자의 의무)
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>서비스의 데이터를 무단으로 수집·복제·배포하는 행위</li>
              <li>AI 분석 결과를 왜곡하거나 상업적으로 오남용하는 행위</li>
              <li>서비스의 정상적인 운영을 방해하는 행위</li>
              <li>관련 법령 및 공공질서에 위반되는 행위</li>
            </ul>
          </div>

          {/* 제7조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제7조 (지적재산권)
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>서비스에 포함된 모든 콘텐츠의 저작권 및 지적재산권은 서비스 제공자 또는 정당한 권리자에게 귀속됩니다.</li>
              <li>이용자는 서비스의 콘텐츠를 개인적·비상업적 목적에 한하여 이용할 수 있습니다.</li>
              <li>사전 동의 없이 콘텐츠를 재가공, 재배포, 상업적으로 이용할 수 없습니다.</li>
            </ul>
          </div>

          {/* 제8조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제8조 (AI 분석 결과의 성격)
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>서비스에서 제공하는 AI 기반 분석, 가격 판단, 추천 결과는 통계적·확률적 모델에 기반한 참고 정보입니다.</li>
              <li>해당 결과는 실거래 가격, 계약 성사 여부, 투자 수익을 보장하지 않습니다.</li>
              <li>데이터 수집 시점, 모델 구조, 시장 변화에 따라 실제 결과와 차이가 발생할 수 있습니다.</li>
            </ul>
          </div>

          {/* 제9조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제9조 (매물 정보 및 책임의 한계)
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>서비스에 표시되는 매물 정보는 공개 데이터, 제휴 정보, 통계 분석을 기반으로 제공됩니다.</li>
              <li>서비스는 매물 정보의 완전성, 최신성, 정확성을 보장하지 않습니다.</li>
              <li>이용자가 본 서비스를 통해 얻은 정보를 근거로 부동산 거래 또는 계약을 진행함에 따라 발생한 손해에 대해 서비스는 책임을 지지 않습니다.</li>
            </ul>
          </div>

          {/* 제10조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제10조 (책임의 제한)
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>서비스는 천재지변, 시스템 장애, 데이터 제공자의 사정 등 불가항력적인 사유로 서비스를 제공할 수 없는 경우 책임을 지지 않습니다.</li>
              <li>서비스는 이용자의 부동산 거래, 투자 결과에 대해 어떠한 책임도 부담하지 않습니다.</li>
              <li>이용자가 서비스의 정보를 신뢰하여 발생한 손해에 대해 서비스는 고의 또는 중과실이 없는 한 책임을 지지 않습니다.</li>
            </ul>
          </div>

          {/* 제11조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제11조 (서비스의 중단)
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>서비스는 시스템 점검, 유지보수, 운영 정책 변경 등의 사유로 서비스 제공을 일시적으로 중단할 수 있습니다.</li>
              <li>서비스 중단 시 사전 공지를 원칙으로 하나, 긴급한 경우 사후 공지할 수 있습니다.</li>
            </ul>
          </div>

          {/* 제12조 */}
          <div className="border-l-4 border-slate-200 pl-4">
            <h2 className="text-lg font-semibold text-slate-800">
              제12조 (준거법 및 관할)
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>본 약관은 대한민국 법령을 준거법으로 합니다.</li>
              <li>서비스 이용과 관련하여 발생한 분쟁에 대해서는 서비스 제공자의 소재지를 관할하는 법원을 전속 관할로 합니다.</li>
            </ul>
          </div>

          {/* 부칙 */}
          <div className="border-t border-slate-200 pt-6 text-sm text-slate-600">
            <h2 className="font-semibold text-slate-800">부칙</h2>
            <p className="mt-2">
              본 약관은 서비스 최초 공개일로부터 적용됩니다.
            </p>
          </div>

        </div>
      </section>
    </main>
  );
}
