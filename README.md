# drAIver

Une IA qui regarde l'écran et conduit une voiture dans le jeu [Slow Roads](https://slowroads.io).

Le programme capture l'écran 15 fois par seconde, envoie chaque image à un réseau de neurones qui décide de combien tourner, puis transmet cette décision au jeu via une manette virtuelle. L'accélérateur est fixe : l'IA gère uniquement la direction.

---

## Sommaire

1. [Le principe en bref](#1-le-principe-en-bref)
2. [Les technologies utilisées](#2-les-technologies-utilisées)
3. [Installation](#3-installation)
4. [Utilisation](#4-utilisation)
5. [Le dataset](#5-le-dataset)
6. [Le parcours d'une image](#6-le-parcours-dune-image)
7. [Le réseau de neurones](#7-le-réseau-de-neurones)
8. [L'entraînement](#8-lentraînement)
9. [Les résultats](#9-les-résultats)
10. [Les fichiers du projet](#10-les-fichiers-du-projet)
11. [Limites et suite du projet](#11-limites-et-suite-du-projet)

---

## 1. Le principe en bref

On utilise l'**apprentissage supervisé par imitation**, aussi appelé *behavioral cloning*. L'idée est simple : un humain conduit, on enregistre ce qu'il voit et ce qu'il fait, puis on apprend à un réseau de neurones à reproduire ses gestes.

Le projet se déroule en trois phases :

```
1. ENREGISTRER    On conduit à la manette
   recorder.py -> dataset/ (images + valeurs de la manette)

2. ENTRAÎNER      Le réseau apprend à nous imiter
   train.py    -> model.pth (le modèle entraîné) + loss.png (la courbe)

3. CONDUIRE       L'IA conduit seule
   main.py     <- charge model.pth
```

À chaque image, le réseau répond à une seule question : **« sur cette image, de combien faut-il tourner ? »** Sa réponse est un nombre entre –1 (à fond à gauche) et +1 (à fond à droite).

> **Imitation ou renforcement ?** Ici, le modèle copie un humain : c'est de l'apprentissage **supervisé**. L'apprentissage **par renforcement** (RL), où l'IA apprend seule par essais et erreurs avec un système de récompenses, est l'objectif de la suite du projet.

---

## 2. Les technologies utilisées

| Technologie | Rôle dans le projet |
|---|---|
| **Python 3.12** | Langage de tout le projet |
| **uv** | Gestionnaire de projet : installe Python, les librairies et l'environnement virtuel (`.venv`) en une commande |
| **PyTorch** (`torch`) | Création, entraînement, sauvegarde et utilisation du réseau de neurones, sur la carte graphique (CUDA) si elle est disponible |
| **OpenCV** (`cv2`) | Lecture, écriture, redimensionnement et conversion de couleurs des images |
| **NumPy** | Manipulation des images et des valeurs sous forme de tableaux de nombres |
| **mss** | Capture d'écran rapide |
| **pygame** | Lecture de la manette PS4 pendant l'enregistrement |
| **vgamepad** + **ViGEmBus** | Création d'une fausse manette Xbox que le jeu croit réelle. vgamepad est la librairie Python, ViGEmBus le pilote Windows qu'elle utilise |
| **Matplotlib** | Tracé de la courbe d'apprentissage |
| **ctypes** (inclus dans Python) | Lecture du clavier même quand le jeu est au premier plan, via la fonction Windows `GetAsyncKeyState` |
| **winsound** (inclus dans Python) | Bips de début et de fin d'enregistrement |

Le projet fonctionne **uniquement sous Windows**, à cause de ViGEmBus, `ctypes.windll` et `winsound`.

---

## 3. Installation

### Prérequis

- Windows 10 ou 11.
- **uv**. S'il n'est pas installé, lancez la commande suivante, puis rouvrez le terminal :
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- Le pilote **ViGEmBus**. Pour vérifier qu'il est installé :
  ```powershell
  sc.exe query ViGEmBus
  ```
  Le service doit être à l'état `RUNNING`. Sinon, installez-le depuis [les releases de ViGEmBus](https://github.com/nefarius/ViGEmBus/releases), puis redémarrez le PC.
- Une carte graphique NVIDIA est conseillée pour l'entraînement, mais **pas obligatoire pour conduire** : sans elle, le modèle tourne sur le processeur.

### Installer le projet

Depuis le dossier du projet :

```powershell
uv sync
```

Cette commande crée le `.venv` et installe toutes les librairies, dont PyTorch avec CUDA 12.8. Le téléchargement est volumineux.

Pour vérifier que PyTorch voit la carte graphique :

```powershell
uv run python -c "import torch; print(torch.cuda.is_available())"
```

`True` signifie que la carte graphique sera utilisée, `False` que ce sera le processeur.

---

## 4. Utilisation

### Préparer le jeu

1. Ouvrez [slowroads.io](https://slowroads.io) dans le navigateur.
2. Passez en **vrai plein écran** avec F11.
3. Utilisez les mêmes réglages et la **même caméra** que pendant l'enregistrement. Les captures du dossier `settings/` servent de référence.
4. Mettez le jeu sur l'**écran principal**, celui que le programme capture.

### Faire conduire l'IA

```powershell
uv run python main.py
```

Le programme démarre en **mode manuel**. Les flèches du clavier pilotent la manette virtuelle, ce qui permet de vérifier, ou de refaire, l'assignation des commandes dans le jeu avant de lancer l'IA.

| Touche | Action |
|---|---|
| ↑ | Accélérer à fond |
| ↓ | Freiner à fond |
| ← / → | Tourner à fond à gauche / à droite |
| **Entrée** | Activer ou couper l'IA |
| `Ctrl+C` dans le terminal | Quitter et relâcher la manette virtuelle |

**Conseils :**

- **Manette physique :** éteignez-la, sinon le jeu risque de la lire à la place de la manette virtuelle.
- **Pendant la conduite :** gardez une main sur Entrée. Si la voiture part dans l'herbe, un appui vous rend immédiatement le contrôle.
- **Vitesse :** elle se règle avec `THROTTLE`, en haut de `main.py`, réglé à `0.4`. Une vitesse plus basse facilite les virages.
- **`Lag detected` :** si ce message s'affiche souvent, la machine n'arrive pas à tenir les 15 images/s. Fermez les autres applications.

### Enregistrer de nouvelles données

Branchez une manette PS4, puis lancez :

```powershell
uv run python recorder.py
```

| Action | Effet |
|---|---|
| **Carré** | Démarre un clip, avec 2 bips aigus |
| **Carré** à nouveau | Arrête le clip, avec 1 long bip grave |
| `Ctrl+C` | Quitte le programme |

Seul ce qui se passe entre deux appuis sur carré est enregistré. Chaque clip est sauvegardé dans son propre dossier : `dataset/recovery/run_<date>_<heure>/`. Un clip raté se supprime simplement en effaçant son dossier.

Pour vérifier que la manette est bien lue :

```powershell
uv run python test.py
```

### Réentraîner le modèle

```powershell
uv run python train.py
```

Le script écrase `model.pth` et `loss.png`. Pensez à **copier l'ancien `model.pth`** avant de réentraîner si vous voulez pouvoir revenir en arrière. L'entraînement prend environ 2 à 3 minutes sur une RTX 3060 Ti.

---

## 5. Le dataset

Le dataset **n'est pas sur GitHub**, car il est trop volumineux (environ 420 Mo) et ignoré par `.gitignore`. Il faut le récupérer auprès de l'équipe et le placer ainsi :

```
dataset/
├── dataset/                      conduite normale
│   ├── run_20261007_164612/
│   ├── run_20261025_145602/
│   └── ...                       8 sessions
└── recovery/                     clips de récupération
    ├── run_20261102_213727/
    └── ...                       128 clips
```

Il n'est nécessaire que pour **réentraîner** : `model.pth` suffit pour faire conduire l'IA.

### Le contenu d'une session

```
run_20261025_152111/
├── img/
│   ├── 00000.jpg        une image toutes les 1/15 de seconde
│   ├── 00001.jpg
│   └── ...
└── driving_log.csv
```

`driving_log.csv` contient une ligne par image :

```
image_path,     steering, throttle, brake
img\00000.jpg,  -0.214,   1.0,      0.0
```

| Colonne | Signification | Valeurs |
|---|---|---|
| `image_path` | Image correspondante | Chemin relatif |
| `steering` | Direction | –1 (gauche) à +1 (droite) |
| `throttle` | Accélérateur | 0 à 1 |
| `brake` | Frein | 0 à 1 |

Seule la colonne `steering` sert à l'entraînement pour l'instant.

### Deux types de données

| | Conduite normale | Clips de récupération |
|---|---|---|
| **Contenu** | Conduite propre, sans sortie de route | La voiture part du bord de la route ou de l'herbe, et y revient |
| **Quantité** | 8 sessions, **47 842 images**, environ 53 minutes | 128 clips, **4 300 images**, environ 5 minutes |
| **Durée par enregistrement** | 1 à 10 minutes | 1 à 5 secondes |
| **Répartition** | — | Moitié depuis la droite, moitié depuis la gauche |

**Au total : 52 142 images**, de 128 × 72 pixels.

### Pourquoi des clips de récupération ?

Si le modèle n'apprend qu'à partir d'une conduite parfaite, il ne voit jamais à quoi ressemble une voiture mal placée. Or, en conduisant seul, il dérive forcément un peu, et se retrouve alors dans une situation inconnue : il ne sait pas revenir, et il sort de la route.

Les clips de récupération lui montrent quoi faire dans ces cas-là. Pour qu'ils soient utiles, on a suivi quelques règles :

- **Rien d'autre que le retour :** seul le retour vers la route est enregistré, jamais la sortie volontaire. Sinon, le modèle apprendrait aussi à sortir.
- **Départ :** on appuie sur carré juste avant de braquer vers la route.
- **Fin :** on arrête une fois la voiture stabilisée.
- **Variété :** les clips sont pris des deux côtés, en ligne droite et en virage.
- **Tri :** les clips où l'on braquait d'abord dans le mauvais sens ont été supprimés, puis refaits.

---

## 6. Le parcours d'une image

Une image change de forme plusieurs fois avant d'arriver au réseau :

| Étape | Forme | Ce qui se passe |
|---|---|---|
| Capture d'écran (`mss`) | hauteur × largeur × 4 | Pixels bruts de l'écran, en couleurs BGRA |
| `recorder.py` ou `main.py` | 72 × 128 × 3 | Suppression du canal de transparence et réduction en 128 × 72. C'est ce format qui est enregistré en JPG |
| `process_frame` (`processing.py`) | 27 × 128 × 3 | Retire 26 lignes en haut (le ciel) et 19 en bas (le capot), passe les couleurs en YUV et ramène les valeurs entre 0 et 1 |
| `train.py` ou `main.py` | 3 × 27 × 128 | Format attendu par PyTorch : les canaux de couleur passent en premier |
| Lot d'entraînement | 128 × 3 × 27 × 128 | 128 images traitées en même temps |
| Sortie du réseau | 1 nombre par image | La direction, entre –1 et 1 |

**Point essentiel :** `train.py` et `main.py` utilisent **la même fonction `process_frame`**. Le réseau voit donc exactement le même type d'image pendant l'entraînement et pendant la conduite. Si cette préparation change, il faut réentraîner le modèle.

**Pourquoi le YUV ?** Ce format sépare la luminosité (Y) des couleurs (U et V). C'est le choix de PilotNet, le modèle de NVIDIA dont on s'est inspiré, et il aide à distinguer la route grise de l'herbe verte.

---

## 7. Le réseau de neurones

Le réseau est défini dans `model.py`. Il s'agit d'un **réseau de neurones convolutif** (CNN) inspiré de **PilotNet**, un modèle de NVIDIA pour la conduite autonome.

Il compte deux blocs. Les **convolutions** repèrent des motifs dans l'image, comme les bords ou la route. Les **couches linéaires** transforment ces motifs en une décision.

```
3 × 27 × 128     image d'entrée (Y, U, V)
      │
24 × 14 × 64     convolution 5×5 + ReLU        ┐
36 × 7 × 32      convolution 5×5 + ReLU        │ extraction de motifs
48 × 4 × 16      convolution 3×3 + ReLU        │ (features)
64 × 4 × 16      convolution 3×3 + ReLU        ┘
      │
4096 valeurs     mise à plat (Flatten)
100              linéaire + ReLU + Dropout     ┐
50               linéaire + ReLU               │ décision
1                linéaire + Tanh               ┘ (regressor)
      │
direction entre –1 et +1
```

| Élément | Rôle |
|---|---|
| **Convolution** (`Conv2d`) | Fait glisser de petits filtres sur l'image pour repérer des motifs. Chaque filtre apprend à reconnaître quelque chose |
| **`stride=2`** | Le filtre avance de 2 pixels : l'image est divisée par 2 à chaque couche |
| **ReLU** | Remplace les valeurs négatives par 0. Sans elle, le réseau ne pourrait apprendre que des relations très simples |
| **Flatten** | Transforme le bloc 64 × 4 × 16 en une liste de 4 096 valeurs |
| **Linéaire** (`Linear`) | Relie chaque entrée à chaque sortie avec un poids |
| **Dropout(0.3)** | Pendant l'entraînement, éteint 30 % des neurones au hasard, pour limiter l'apprentissage par cœur. Il est désactivé pendant la conduite |
| **Tanh** | Ramène la sortie entre –1 et 1, la plage de la direction |

Le réseau contient **481 573 paramètres**, c'est-à-dire des nombres réglés pendant l'entraînement.

### Le fichier `model.pth`

- **`model.py` est le plan :** il décrit les couches et leur enchaînement.
- **`model.pth` contient les réglages :** ce sont les 481 573 nombres trouvés pendant l'entraînement, soit environ 2 Mo.

L'un ne fonctionne pas sans l'autre. Le plan seul donne un réseau aux valeurs aléatoires, qui conduit n'importe comment. C'est pourquoi `main.py` fait :

```python
model = SteeringNet()                                # construit le réseau d'après le plan
model.load_state_dict(torch.load("model.pth"))       # lui donne ce qu'il a appris
model.eval()                                         # passe en mode conduite (désactive le Dropout)
```

Si on modifie les couches dans `model.py`, l'ancien `model.pth` ne se charge plus : il faut réentraîner.

---

## 8. L'entraînement

`train.py` fonctionne en plusieurs étapes.

### 1. Charger les données

Il lit toutes les sessions et tous les clips, passe chaque image dans `process_frame` et associe chaque image à sa direction.

### 2. Lisser la direction

À la manette, la direction est saccadée : elle change en moyenne de 0,16 d'une image à l'autre. On applique une **moyenne glissante sur 5 images** pour adoucir ces à-coups. Elle est calculée à l'intérieur de chaque session, pour ne pas mélanger des enregistrements sans rapport.

### 3. Séparer entraînement et test

Une partie des données est mise de côté et **jamais montrée au modèle pendant l'apprentissage**. Elle sert à vérifier qu'il sait généraliser à des images nouvelles :

- **Conduite normale :** toute la session `run_20261025_152111`.
- **Récupération :** 1 clip sur 10.

Cela donne **46 139 images d'entraînement et 6 003 images de test**.

On sépare **par session entière**, et non image par image. Deux images consécutives sont presque identiques : si l'une était en entraînement et sa voisine en test, le test serait trop facile, et le score trompeur.

### 4. Rééquilibrer

Les clips de récupération ne représentent qu'environ 8 % des images. Un `WeightedRandomSampler` les tire plus souvent, pour qu'ils pèsent **25 % de chaque lot**. Le modèle apprend ainsi vraiment à revenir sur la route.

### 5. Augmenter les données

Une image sur deux est **retournée en miroir**, avec la direction de signe opposé. Une route qui tourne à gauche devient une route qui tourne à droite. Le modèle voit ainsi plus de situations différentes, et reste équilibré entre la gauche et la droite.

### 6. Apprendre

Le réseau apprend sur **20 epochs**, une epoch étant un passage complet sur les données. Les images lui sont données par lots de 128, avec l'optimiseur **Adam**.

Pour chaque lot, il répète 4 étapes :

```python
optimizer.zero_grad()      # 1. efface les calculs du lot précédent
loss = mse_loss(...)       # 2. mesure l'erreur
loss.backward()            # 3. calcule comment chaque paramètre a contribué à l'erreur
optimizer.step()           # 4. ajuste un peu les paramètres pour réduire l'erreur
```

### 7. Garder le meilleur modèle

Après chaque epoch, le modèle est évalué sur les données de test. Il n'est sauvegardé dans `model.pth` que s'il bat son meilleur score : le fichier final contient donc la **meilleure** epoch, pas forcément la dernière.

### Qu'est-ce que la loss ?

La **loss**, ou fonction de perte, est une **note d'erreur** : plus elle est basse, mieux le modèle prédit. C'est la valeur que l'entraînement cherche à faire baisser.

On utilise la **MSE**, ou erreur quadratique moyenne. Pour chaque image, on calcule l'écart entre la prédiction et la vraie valeur, on le met au carré, puis on fait la moyenne.

| Direction réelle | Prédiction | Écart | Écart au carré |
|---|---|---|---|
| 0,5 | 0,2 | 0,3 | 0,09 |
| –0,8 | –0,7 | 0,1 | 0,01 |
| | | **MSE** | **(0,09 + 0,01) / 2 = 0,05** |

Le carré rend toutes les erreurs positives, et pénalise plus fortement les grosses erreurs.

### Les principaux réglages

Ils sont en haut de `train.py` :

| Réglage | Valeur | Signification |
|---|---|---|
| `EPOCHS` | 20 | Nombre de passages sur les données |
| `BATCH_SIZE` | 128 | Nombre d'images par lot |
| `LEARNING_RATE` | 0.001 | Taille des ajustements à chaque étape |
| `SMOOTHING_WINDOW` | 5 | Nombre d'images de la moyenne glissante |
| `RECOVERY_SHARE` | 0.25 | Part des clips de récupération dans chaque lot |

---

## 9. Les résultats

### La courbe d'apprentissage (`loss.png`)

- **Courbe d'entraînement :** l'erreur sur les images apprises. Elle passe d'environ 0,13 à 0,03.
- **Courbe de test :** l'erreur sur les images jamais vues. Elle se stabilise vers 0,06 à partir de la 7ᵉ epoch.

L'écart entre les deux montre que le modèle commence à **apprendre par cœur** les images d'entraînement (*overfitting*). C'est sans gravité ici, car l'erreur de test ne remonte pas vraiment, et c'est le meilleur modèle sur le test qui est conservé.

### Les scores sur les données de test

| Données de test | Erreur du modèle (MSE) | Erreur si on ne tournait jamais | Bon sens de braquage* |
|---|---|---|---|
| Conduite normale (5 477 images) | **0,034** | 0,167 | **98 %** |
| Récupération (526 images) | **0,125** | 0,290 | **89 %** |

*\*Sur les images où le conducteur braquait nettement, au-delà de ±0,3.*

- **Conduite normale :** l'erreur du modèle est environ **5 fois plus faible** que celle d'un modèle qui ne tournerait jamais.
- **Récupération :** c'est plus difficile, avec des situations rares et des gestes rapides, mais le modèle braque dans le bon sens 9 fois sur 10.

### Dans le jeu

Le vrai test se fait dans le jeu, car un bon score sur des images enregistrées ne prouve pas que la voiture conduit bien. **La voiture suit la route de façon autonome**, et le modèle a été testé avec succès sur deux PC différents.

---

## 10. Les fichiers du projet

| Fichier | Rôle |
|---|---|
| `main.py` | **Conduite par l'IA** : capture l'écran, prédit la direction et commande la manette virtuelle. Contient aussi le mode manuel aux flèches |
| `recorder.py` | **Enregistrement** du dataset, déclenché par la touche carré |
| `train.py` | **Entraînement** du modèle |
| `model.py` | **Architecture** du réseau de neurones |
| `processing.py` | **Préparation des images** (crop, YUV, normalisation), commune à l'entraînement et à la conduite |
| `model.pth` | **Modèle entraîné** : les paramètres appris |
| `loss.png` | **Courbe d'apprentissage** du dernier entraînement |
| `test.py` | Affiche les valeurs de la manette PS4, pour vérifier qu'elle est bien lue |
| `simulation.py` | Premier test de la manette virtuelle, qui envoie de faux mouvements au jeu |
| `settings/` | Captures des réglages du jeu utilisés |
| `pyproject.toml` / `uv.lock` | Liste des dépendances et versions exactes, utilisées par `uv sync` |

Comment les fichiers s'emboîtent :

```
recorder.py ──────────► dataset/
                           │
processing.py ──┐          ▼
model.py ───────┼──► train.py ──► model.pth, loss.png
                │                    │
                └──► main.py ◄───────┘
                        │
                        ▼
                manette virtuelle ──► Slow Roads
```

---

## 11. Limites et suite du projet

### Limites actuelles

- **Accélérateur et frein :** l'IA ne les gère pas. L'accélérateur est fixe, et le frein jamais utilisé.
- **Mémoire :** le modèle regarde **une seule image à la fois**, sans mémoire des précédentes. Il ne perçoit donc ni la vitesse ni le mouvement.
- **Reproduction des erreurs :** le modèle imite le conducteur, y compris ses imperfections, comme les coups de volant brusques.
- **Récupération :** sur ces situations, la précision reste plus faible qu'en conduite normale.

### Pistes d'amélioration

1. **Prédire l'accélérateur**, en ajoutant une deuxième sortie au réseau.
2. **Empiler les 2 ou 3 dernières images** en entrée, pour que le modèle perçoive le mouvement.
3. **Enrichir le dataset** avec plus de virages serrés, d'autres décors, ou d'autres moments de la journée.
4. **Passer à l'apprentissage par renforcement**, l'objectif final : l'IA apprendrait seule par essais et erreurs, à partir d'une récompense, comme le temps passé sur la route. Le modèle actuel pourrait lui servir de point de départ.
