/**
 * google_form.gs — «Kirayə Kompası» saytı üçün rəy sorğusu (Google Apps Script).
 * script.google.com → yeni layihə → bu kodu yapışdırın → main funksiyasını işlədin.
 *
 * 1) Sorğunu yaradır (anonim, e-poçt toplanmır).
 * 2) Prototipi nümayiş etdirmək üçün 12 test cavabı göndərir (AI agentlərin rolları) —
 *    statistika səhifəsi necə görünəcəyini göstərmək üçün; tədqiqat məlumatı deyil.
 * 3) Linkləri Execution log-a yazır.
 */
const SITE = 'https://kiraye-kompasi.streamlit.app';
const SECTIONS = ['Kalkulyator', 'Xəritə və rayonlar', 'Necə ucuzlaşdırmaq olar (addım-addım)',
                  'Real elanlar', 'AI məsləhətçi', 'Bazar bir baxışda'];

function main() {
  const form = FormApp.create('Kirayə Kompası — sayt haqqında rəyiniz');
  form.setDescription(
    'Sayt: ' + SITE + '\n' +
    'Saytı 2–3 dəqiqə sınayın və 7 qısa suala cavab verin (1 dəqiqə). Sorğu anonimdir — e-poçt toplanmır.\n' +
    'Data final layihəsi: bina.az elanları → Python → Oracle SQL → Power BI → Streamlit + Gemini.');
  form.setCollectEmail(false);
  form.setAllowResponseEdits(false);
  form.setShowLinkToRespondAgain(false);
  form.setConfirmationMessage('Təşəkkür edirik! Rəyiniz layihəni yaxşılaşdırmağa kömək edəcək.');

  const qWho = form.addMultipleChoiceItem().setTitle('Siz kimsiniz?')
    .setChoiceValues(['Kirayədə yaşayıram', 'Kirayə mənzil axtarıram', 'Ev sahibiyəm (kirayə verirəm)',
                      'Vasitəçiyəm (rieltor)', 'Digər']).setRequired(true);
  const qClear = form.addScaleItem().setTitle('Sayt maaş və kirayə vəziyyətinizi anlamağa kömək etdi?')
    .setBounds(1, 5).setLabels('Heç', 'Çox').setRequired(true);
  const qReal = form.addMultipleChoiceItem().setTitle('Kalkulyatorun nəticəsi real təcrübənizə uyğun gəlir?')
    .setChoiceValues(['Bəli', 'Qismən', 'Xeyr', 'Bilmirəm']).setRequired(true);
  const qAi = form.addScaleItem().setTitle('AI məsləhətçinin izahı nə dərəcədə faydalı idi?')
    .setHelpText('«Vəziyyətimi izah et» düyməsi və ya sual vermək.')
    .setBounds(1, 5).setLabels('Faydasız', 'Çox faydalı').setRequired(true);
  const qBest = form.addCheckboxItem().setTitle('Ən faydalı bölmə hansıdır? (bir neçəsini seçə bilərsiniz)')
    .setChoiceValues(SECTIONS).setRequired(true);
  const qRec = form.addScaleItem().setTitle('Saytı dostunuza tövsiyə edərdiniz?')
    .setBounds(1, 5).setLabels('Heç vaxt', 'Mütləq').setRequired(true);
  const qIdea = form.addParagraphTextItem().setTitle('Nəyi əlavə etmək və ya yaxşılaşdırmaq olar?');

  try { form.setPublished(true); } catch (e) { /* köhnə versiyada lazım deyil */ }
  form.setAcceptingResponses(true);

  // ---- Prototip üçün test cavabları (AI agentlərin rolları)
  const tests = [
    // [kim, aydınlıq 1-5, uyğun?, AI 1-5, faydalı bölmələr (SECTIONS indeksləri), tövsiyə 1-5, təklif]
    ['Kirayə mənzil axtarıram', 5, 'Bəli', 5, [0, 1, 2], 5, 'Metro stansiyasına görə filtr olsa əla olar.'],
    ['Kirayədə yaşayıram', 4, 'Bəli', 4, [0, 2], 4, 'Kommunal xərcləri də büdcəyə əlavə etmək olar.'],
    ['Kirayə mənzil axtarıram', 5, 'Qismən', 5, [0, 4], 5, ''],
    ['Kirayədə yaşayıram', 4, 'Bəli', 3, [1, 3], 4, 'Elanların şəkli görünsə rahat olar.'],
    ['Ev sahibiyəm (kirayə verirəm)', 4, 'Qismən', 4, [1, 5], 3, 'Ev sahibləri üçün «mənzilimi neçəyə verim» bölməsi.'],
    ['Vasitəçiyəm (rieltor)', 3, 'Qismən', 3, [5], 3, 'Vasitəçi faizini ayrıca göstərmək olar.'],
    ['Kirayə mənzil axtarıram', 5, 'Bəli', 5, [0, 2, 4], 5, 'Rus dilində versiya da olsun.'],
    ['Kirayədə yaşayıram', 4, 'Bəli', 4, [0, 1], 4, ''],
    ['Digər', 4, 'Bilmirəm', 4, [5, 1], 4, 'Qiymətin aylar üzrə dəyişməsini qrafikdə görmək istərdim.'],
    ['Kirayə mənzil axtarıram', 3, 'Xeyr', 4, [3], 3, 'Mobil telefonda xəritə bir az kiçik görünür.'],
    ['Kirayədə yaşayıram', 5, 'Bəli', 5, [0, 2, 3], 5, 'Yeni elan çıxanda bildiriş göndərsin.'],
    ['Kirayə mənzil axtarıram', 4, 'Qismən', 4, [0, 4], 4, ''],
  ];
  tests.forEach(t => {
    const r = form.createResponse()
      .withItemResponse(qWho.createResponse(t[0]))
      .withItemResponse(qClear.createResponse(t[1]))
      .withItemResponse(qReal.createResponse(t[2]))
      .withItemResponse(qAi.createResponse(t[3]))
      .withItemResponse(qBest.createResponse(t[4].map(i => SECTIONS[i])))
      .withItemResponse(qRec.createResponse(t[5]));
    if (t[6]) r.withItemResponse(qIdea.createResponse(t[6]));
    r.submit();
  });

  const url = form.getPublishedUrl();
  let short = url;
  try { short = form.shortenFormUrl(url); } catch (e) {}
  Logger.log('FORM_LINK=' + short);
  Logger.log('EDIT_LINK=' + form.getEditUrl());
  Logger.log('TEST_RESPONSES=' + form.getResponses().length);
}
