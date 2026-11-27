---
license: apache-2.0
task_categories:
- robotics
tags:
- LeRobot
configs:
- config_name: default
  data_files: data/*/*.parquet
---

This dataset was created using [LeRobot](https://github.com/huggingface/lerobot).


<a class="flex" href="https://huggingface.co/spaces/lerobot/visualize_dataset?path=lerobot/roboturk">
<img class="block dark:hidden" src="https://huggingface.co/datasets/huggingface/badges/resolve/main/visualize-this-dataset-xl.svg"/>
<img class="hidden dark:block" src="https://huggingface.co/datasets/huggingface/badges/resolve/main/visualize-this-dataset-xl-dark.svg"/>
</a>


## Dataset Description



- **Homepage:** [More Information Needed]
- **Paper:** [More Information Needed]
- **License:** apache-2.0

## Dataset Structure

[meta/info.json](meta/info.json):
```json
{
    "codebase_version": "v3.0",
    "robot_type": "unknown",
    "total_episodes": 1995,
    "total_frames": 187507,
    "total_tasks": 3,
    "chunks_size": 1000,
    "fps": 10,
    "splits": {
        "train": "0:1995"
    },
    "data_path": "data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet",
    "video_path": "videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4",
    "features": {
        "observation.images.front_rgb": {
            "dtype": "video",
            "shape": [
                480,
                640,
                3
            ],
            "names": [
                "height",
                "width",
                "channel"
            ],
            "video_info": {
                "video.fps": 10.0,
                "video.codec": "av1",
                "video.pix_fmt": "yuv420p",
                "video.is_depth_map": false,
                "has_audio": false
            }
        },
        "observation.state": {
            "dtype": "float32",
            "shape": [
                8
            ],
            "names": {
                "motors": [
                    "motor_0",
                    "motor_1",
                    "motor_2",
                    "motor_3",
                    "motor_4",
                    "motor_5",
                    "motor_6",
                    "motor_7"
                ]
            },
            "fps": 10
        },
        "action": {
            "dtype": "float32",
            "shape": [
                7
            ],
            "names": {
                "motors": [
                    "motor_0",
                    "motor_1",
                    "motor_2",
                    "motor_3",
                    "motor_4",
                    "motor_5",
                    "motor_6"
                ]
            },
            "fps": 10
        },
        "timestamp": {
            "dtype": "float32",
            "shape": [
                1
            ],
            "names": null,
            "fps": 10
        },
        "episode_index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null,
            "fps": 10
        },
        "frame_index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null,
            "fps": 10
        },
        "next.reward": {
            "dtype": "float32",
            "shape": [
                1
            ],
            "names": null,
            "fps": 10
        },
        "next.done": {
            "dtype": "bool",
            "shape": [
                1
            ],
            "names": null,
            "fps": 10
        },
        "index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null,
            "fps": 10
        },
        "task_index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null,
            "fps": 10
        }
    },
    "data_files_size_in_mb": 100,
    "video_files_size_in_mb": 200
}
```


## Citation

**BibTeX:**

```bibtex
[More Information Needed]
```