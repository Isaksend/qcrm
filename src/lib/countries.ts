/** Справочник стран: ISO2, русское название, телефонный код (только цифры, без +). */
export interface CountryDial {
  iso2: string
  name: string
  dial: string
}

export const COUNTRIES: CountryDial[] = [
  { iso2: 'KZ', name: 'Казахстан', dial: '7' },
  { iso2: 'RU', name: 'Россия', dial: '7' },
  { iso2: 'BY', name: 'Беларусь', dial: '375' },
  { iso2: 'UA', name: 'Украина', dial: '380' },
  { iso2: 'UZ', name: 'Узбекистан', dial: '998' },
  { iso2: 'KG', name: 'Кыргызстан', dial: '996' },
  { iso2: 'TJ', name: 'Таджикистан', dial: '992' },
  { iso2: 'TM', name: 'Туркменистан', dial: '993' },
  { iso2: 'AZ', name: 'Азербайджан', dial: '994' },
  { iso2: 'AM', name: 'Армения', dial: '374' },
  { iso2: 'GE', name: 'Грузия', dial: '995' },
  { iso2: 'MD', name: 'Молдова', dial: '373' },
  { iso2: 'US', name: 'США', dial: '1' },
  { iso2: 'GB', name: 'Великобритания', dial: '44' },
  { iso2: 'DE', name: 'Германия', dial: '49' },
  { iso2: 'FR', name: 'Франция', dial: '33' },
  { iso2: 'IT', name: 'Италия', dial: '39' },
  { iso2: 'ES', name: 'Испания', dial: '34' },
  { iso2: 'PL', name: 'Польша', dial: '48' },
  { iso2: 'NL', name: 'Нидерланды', dial: '31' },
  { iso2: 'BE', name: 'Бельгия', dial: '32' },
  { iso2: 'CH', name: 'Швейцария', dial: '41' },
  { iso2: 'AT', name: 'Австрия', dial: '43' },
  { iso2: 'SE', name: 'Швеция', dial: '46' },
  { iso2: 'NO', name: 'Норвегия', dial: '47' },
  { iso2: 'FI', name: 'Финляндия', dial: '358' },
  { iso2: 'TR', name: 'Турция', dial: '90' },
  { iso2: 'AE', name: 'ОАЭ', dial: '971' },
  { iso2: 'SA', name: 'Саудовская Аравия', dial: '966' },
  { iso2: 'IN', name: 'Индия', dial: '91' },
  { iso2: 'CN', name: 'Китай', dial: '86' },
  { iso2: 'JP', name: 'Япония', dial: '81' },
  { iso2: 'KR', name: 'Республика Корея', dial: '82' },
  { iso2: 'SG', name: 'Сингапур', dial: '65' },
  { iso2: 'AU', name: 'Австралия', dial: '61' },
  { iso2: 'CA', name: 'Канада', dial: '1' },
  { iso2: 'BR', name: 'Бразилия', dial: '55' },
  { iso2: 'MX', name: 'Мексика', dial: '52' },
  { iso2: 'AR', name: 'Аргентина', dial: '54' },
  { iso2: 'IL', name: 'Израиль', dial: '972' },
  { iso2: 'EG', name: 'Египет', dial: '20' },
].sort((a, b) => a.name.localeCompare(b.name, 'ru'))

export function getCountryByIso2(iso2: string | null | undefined): CountryDial | undefined {
  if (!iso2) return undefined
  return COUNTRIES.find((c) => c.iso2 === iso2)
}

export function dialForIso2(iso2: string): string {
  return getCountryByIso2(iso2)?.dial ?? '7'
}
