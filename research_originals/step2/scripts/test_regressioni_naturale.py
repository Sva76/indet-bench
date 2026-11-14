"""Regressioni con esempi e controesempi; solo libreria standard, nessuna inferenza."""

import sys

import unittest

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import controlli_semantici_naturale as N
import sel_testC as S
import verifica_selezione_v4 as V

class Naturale(unittest.TestCase):
    def test_decodifica_letterale_conserva_spazi(self):
        # Simula la pulizia attivata di default in alcuni tokenizer HF.
        class TokenizerFinto:
            def decode(self, ids, skip_special_tokens=False, clean_up_tokenization_spaces=True):
                originale = 'The answer is 1929 . Who founded it ?'
                if clean_up_tokenization_spaces:
                    return originale.replace(' .', '.').replace(' ?', '?')
                return originale
        self.assertEqual(S.decodifica_letterale(TokenizerFinto(), [1, 2]),
                         'The answer is 1929 . Who founded it ?')

    def test_tipo_da_tutti_i_riferimenti(self):
        ex = dict(question="Who designed the garden?", answers=dict(text=["the architect Jane Smith", "Jane Smith"], answer_start=[0,14]))
        self.assertEqual(S.riferimento_tipizzato(ex), ("nome", 1))
        ex = dict(question="What year?", answers=dict(text=["1815", "Battle of Waterloo"], answer_start=[0,5]))
        self.assertEqual(S.riferimento_tipizzato(ex), (None, None))

    def test_nascita_e_carica(self):
        self.assertIsNotNone(N.ancoraggio_domanda("When was the chancellor born?", "The chancellor (1862–90) opposed colonies."))
        self.assertIsNone(N.ancoraggio_domanda("When was the chancellor born?", "The chancellor was born in 1815."))

    def test_media_e_cronologia(self):
        self.assertIsNotNone(N.vincoli_quantitativi("What was the average duty?", "As high as 25 million, averaged VALORE_RIMOSSO.", "numero"))
        self.assertIsNone(N.vincoli_quantitativi("How many students?", "The college had VALORE_RIMOSSO students.", "numero"))
        self.assertIsNotNone(N.vincoli_quantitativi("When was the battle?", "Difficulties arose after 1279. The battle was in VALORE_RIMOSSO.", "anno"))
        self.assertIsNone(N.vincoli_quantitativi("When was the battle?", "The battle was in VALORE_RIMOSSO.", "anno"))

    def test_uno_e_un_numero(self):
        self.assertEqual(S.tipo_risposta("one"), "numero")
        self.assertEqual(S.numero_di("one"), 1.0)
        self.assertIn("one", S.valori_stesso_tipo("One student arrived.", "numero"))
        self.assertTrue(S.distrattore_plausibile("one", "two", "numero"))

    def test_risposta_abbreviata_e_aggettivo_geografico(self):
        forme = N.forme_nominali(["Louis Agassiz"], "Louis Agassiz gave lectures.")
        self.assertTrue(any(N.frase_contiene("Agassiz's view of nature.", f) for f in forme))
        self.assertIsNotNone(V.rim_nome_residuo("Louis Agassiz gave lectures.", "Agassiz's view of nature.", ["Louis Agassiz"]))
        forme = N.forme_nominali(["Victoria"], "Victoria is a state.")
        self.assertTrue(any(N.frase_contiene("Victorian fishing crews.", f) for f in forme))
        self.assertIsNotNone(V.rim_nome_residuo("Victoria is a state.", "Victorian fishing crews.", ["Victoria"]))

    def test_anafore_temporali_e_definite(self):
        for dopo in ("It is home to many people.", "The eye crossed the coast.", "In the following years the town expanded.", "A mere half decade later there were houses."):
            self.assertIsNotNone(N.rischio_discorso(["A key event happened in 1914.", dopo], {0}))
        self.assertIsNone(N.rischio_discorso(["A key event happened.", "A school opened in 1920."], {0}))
        self.assertIsNone(N.rischio_discorso(["A key event happened.", "The University of Example opened in 1920."], {0}))

    def test_elenco_e_sottoinsieme(self):
        self.assertTrue(N.elenco_residuo("How many metropolitan areas?", "The areas are: Alpha; Beta; Gamma."))
        self.assertFalse(N.elenco_residuo("How many students?", "The school admits students every year."))
        self.assertTrue(N.sottoinsieme_numerico("How many lines?", "Six of the seven lines run downtown.", "Six"))
        self.assertTrue(N.sottoinsieme_numerico("How many of the six packages?", "Two packages were awarded.", "Two"))
        self.assertFalse(N.sottoinsieme_numerico("How many museums?", "There are 60 museums.", "60"))

    def test_calcolo_tra_frasi(self):
        testo = "Setanta received VALORE_RIMOSSO of the six packages. Sky took the remaining four."
        self.assertIsNotNone(N.aritmetica_residua("How many packages did Setanta receive?", testo, 2))
        self.assertTrue(V.via_calcolo_v("How many packages did Setanta receive?", testo, 2))

    def test_ruolo_nominale_specifico(self):
        ex = dict(title="University_of_Chicago", question="What alumni member wrote the bestseller Before I Fall?", context="")
        other = dict(title="University_of_Chicago", question="What alumni is the Governor of the Bank of Japan?", context="The governor is Masaaki Shirakawa.")
        self.assertFalse(N.prova_distrattore(ex, other, "Masaaki Shirakawa", "persona")[0])
        ex = dict(title="Yuan_dynasty", question="Who led an attack on China?", context="")
        other = dict(title="Yuan_dynasty", question="Who did the Mongols bring to China?", context="Central Asian Muslims served as administrators.")
        self.assertFalse(N.prova_distrattore(ex, other, "Central Asian Muslims", "persona")[0])
        ex = dict(title="Business", question="Who was the founder of the Oracle Corporation?", context="")
        other = dict(title="Business", question="Who was the founder of community organizing?", context="Saul Alinsky was the founder.")
        self.assertFalse(N.prova_distrattore(ex, other, "Saul Alinsky", "persona")[0])
        ex = dict(title="Economics", question="Who wrote The Hidden Prosperity of the Poor?", context="")
        other = dict(title="Economics", question="Who wrote Capital in the Twenty-First Century?", context="Thomas Piketty wrote Capital.")
        self.assertTrue(N.prova_distrattore(ex, other, "Thomas Piketty", "persona")[0])

    def test_decimali_del_selettore(self):
        for risposta, candidato in (("11.1", "180"), ("0.2", "six"), ("94", "8.8"), ("91.3", "700")):
            self.assertFalse(S.distrattore_plausibile(risposta, candidato, "numero"))
        self.assertEqual(S.numero_di("11.1"), 11.1)
        self.assertEqual(S.numero_di("0.2"), 0.2)
        self.assertTrue(S.distrattore_plausibile("94", "100", "numero"))
        self.assertTrue(S.distrattore_plausibile("0.2", "0.3", "numero"))
        self.assertFalse(S.distrattore_plausibile("2500", "4404.5", "numero"))

    def test_confini_frasi_indipendenti(self):
        esempi = (
            '"It opened in 1950."  The site is old.',
            'The hall opened (in 1950.)  The site is old.',
            'The hall opened in the 1950s.  The site is old.',
        )
        for testo in esempi:
            with self.subTest(testo=testo):
                self.assertEqual(len(S.frasi_di(testo)), 2)
                self.assertEqual(len(V.frasi_naturali(testo)), 2)
        testo = 'Arthur H. Compton arrived. The site is old.'
        self.assertEqual(len(S.frasi_di(testo)), 2)
        self.assertEqual(len(V.frasi_naturali(testo)), 2)

    def test_nominali_plural_trattino_possessivo(self):
        for testo in ("Normans came into Scotland.", "A Norman-derived system."):
            self.assertTrue(any(N.frase_contiene(testo, f) for f in N.forme_nominali(["Norman"], testo)))
        self.assertTrue(any(N.frase_contiene("Watt's engine.", f) for f in N.forme_nominali(["Watt"], "Watt invented it.")))
        self.assertFalse(N.frase_contiene("Northumberland", "north"))

    def test_alias_esplicito_e_demonimo(self):
        forme = N.forme_nominali(["Porifera"], "Porifera (sponges) is a group.")
        self.assertIn("sponges", forme)
        self.assertTrue(any(N.frase_contiene("Chinese records", f) for f in N.forme_nominali(["China"], "China")))

    def test_domande_non_univoche(self):
        self.assertIsNotNone(N.domanda_non_univoca("Who was one of the famous residents?"))
        self.assertIsNotNone(N.domanda_non_univoca("What do some researchers believe?"))
        self.assertIsNone(N.domanda_non_univoca("Who designed the library garden?"))

    def test_nomi_completi(self):
        self.assertFalse(N.nome_intero("Napoleon's"))
        self.assertTrue(N.nome_intero("Maria Skłodowska-Curie"))

    def test_classi_nominali(self):
        self.assertEqual(N.classe_precisa("The Rhine and what other river drained the Alps?", "nome", "Danube"), "cosa:river")
        self.assertEqual(N.classe_precisa("Which other city is nearby?", "nome", "Zaltbommel"), "cosa:city")
        self.assertEqual(N.classe_precisa("What entity deals with staff?", "nome", "Civil Service Tribunal"), "cosa:tribunal")
        self.assertEqual(N.classe_precisa("What entity deals with staff?", "nome", "Conciliation Committee"), "cosa:committee")

    def test_somma_residua(self):
        self.assertIsNotNone(N.aritmetica_residua("How many students in total?", "5,792 students, 3,468 students and 5,984 students.", 15244))
        self.assertIsNone(N.aritmetica_residua("How many students?", "There are 4 teachers and 7 rooms.", 30))

    def test_enumerazione(self):
        self.assertTrue(N.elenco_residuo("How many extended metropolitan areas?", "These are Greater Los Angeles and San Diego–Tijuana."))
        self.assertFalse(N.elenco_residuo("When was the town founded?", "These are the parks and gardens."))

    def test_vincolo_geografico(self):
        ex = dict(title="Huguenot", question="Where did Huguenots settle in England?", context="")
        no = dict(title="Huguenot", question="Where did Huguenots settle in Holland?", context="Huguenots settled in Rotterdam in the Netherlands.")
        si = dict(title="Huguenot", question="Where did Huguenots settle in England?", context="Huguenots settled in Norwich in England.")
        self.assertFalse(N.prova_distrattore(ex, no, "Rotterdam", "luogo")[0])
        self.assertTrue(N.prova_distrattore(ex, si, "Norwich", "luogo")[0])

    def test_anafore(self):
        f = ["Refugees came to the city.", "They built workshops.", "The church opened in 1600."]
        self.assertIsNotNone(N.rischio_discorso(f, {0}))
        self.assertIsNone(N.rischio_discorso(f, {2}))

    def test_altri_operatori(self):
        self.assertTrue(N.altre_vie_nominali("Which company provides train service?", "A different railroad operates branchlines."))
        self.assertFalse(N.altre_vie_nominali("When was the town founded?", "A railroad operates here."))

if __name__ == "__main__":
    unittest.main(verbosity=2)
