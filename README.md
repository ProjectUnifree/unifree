# unifree

Migrate Unity projects to other engines!

:warning: This is an early prototype. :warning:

### Features

* Scan source project and detect files eligible for migration
* Use ChatGPT to translate `.cs` files into Godot scripts and Unreal 3D classes. Here is how sample translation looks:
```
  Unity                                                  | Godot                                   
  ------------------------------------------------------ | ------------------------------------------------------
  public class Player : MonoBehaviour                    | class_name Player:
  {                                                      | 
    private SpriteRenderer spriteRenderer;               | var sprite_renderer: SpriteRenderer
    public Sprite[] sprites;                             | var sprites: Array
    private int spriteIndex;                             | var sprite_index: int
                                                         | 
    public float strength = 5f;                          | var strength: float = 5.0
                                                         | 
    private Vector3 direction;                           | var direction: Vector3
                                                         | 
    private void Awake()                                 | func _ready():
    {                                                    |   sprite_renderer = get_node("SpriteRenderer")
      spriteRenderer = GetComponent<SpriteRenderer>();   | 
    }                                                    | func _on_start():
                                                         |   call_deferred("animate_sprite")
    private void Start()                                 |   set_process(true)
    {                                                    | 
      InvokeRepeating(                                   | func _on_enable():
          nameof(AnimateSprite),                         |   var position = transform.position
          0.15f,                                         |   position.y = 0.0
          0.15f                                          |   transform.position = position
      );                                                 |   direction = Vector3.ZERO
    }                                                    | class_name Player:
                                                         | 
    private void OnEnable()                              | var sprite_renderer: SpriteRenderer
    {                                                    | var sprites: Array
      Vector3 position = transform.position;             | var sprite_index: int
      position.y = 0f;                                   | 
      transform.position = position;                     | var strength: float = 5.0
      direction = Vector3.zero;                          | 
    }                                                    | var direction: Vector3
  }                                                      |

```

## Installation and Usage

 | Key                           | Description                                                   
 | ----------------------------- | ------------------------------------------------------------- 
 | `<config_name>`               | Name of the migration. Currently supported: `godot`, `unreal`  
 | `<source_project_dir>`        | Absolute path of the project to migrate                       
 | `<destination_project_dir>`   | Absolute path of where results should be written              

### OS X

```
brew install git python3
curl -0 https://raw.githubusercontent.com/ProjectUnifree/unifree/main/launch.sh | bash
OPENAI_API_KEY=<your_openai_api_key>  ./launch.sh <config_name> <source_project_dir> <destination_project_dir>
```
 
### Windows

Install Git for Windows https://git-scm.com/download/win, then run:

```
git clone https://github.com/ProjectUnifree/unifree
cd unifree
launch.bat <your_openai_api_key> <config_name> <source_project_dir> <destination_project_dir>
```

### Ubuntu/Debian

```
sudo apt install git python3 python3-venv
curl -0 https://raw.githubusercontent.com/ProjectUnifree/unifree/main/launch.sh | bash
OPENAI_API_KEY=<your_openai_api_key> ./launch.sh <config_name> <source_project_dir> <destination_project_dir>
```


### Call To Action

:wave: Join our [Discord server](https://discord.gg/Ee5wJ4JWBQ) for a live discussion!

We are actively seeking for contributors. If are familiar with Unity, Godot, Cocos2d or any other engineers, help us!

Here is what we need help with:

#### Asset Migration

* :exclamation: :exclamation: Migrate Unity assets to GoDot
* :exclamation: :exclamation: Migrate Unity assets to Cocos2d
* What other engines should be implemented?

#### Source Migration

* Experiment with ChatGPT prompts for better code translation
* Add prompts/configs to migrate to Cocos2d
* What other engines should be implemented?

#### Framework

* :exclamation: Step-by-step console based migration wizard
* :exclamation: More edge case handling
* Architecture review and improvements
