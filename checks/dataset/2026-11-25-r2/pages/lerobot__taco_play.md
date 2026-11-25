---
license: cc-by-4.0
task_categories:
- robotics
tags:
- LeRobot
configs:
- config_name: default
  data_files: data/*/*.parquet
---

This dataset was created using [LeRobot](https://github.com/huggingface/lerobot).

## Dataset Description



- **Homepage:** https://www.kaggle.com/datasets/oiermees/taco-robot
- **Paper:** https://arxiv.org/abs/2209.08959, https://arxiv.org/abs/2210.01911
- **License:** cc-by-4.0

## Dataset Structure

[meta/info.json](meta/info.json):
```json
{
    "codebase_version": "v2.0",
    "robot_type": "unknown",
    "total_episodes": 3603,
    "total_frames": 237798,
    "total_tasks": 406,
    "total_videos": 7206,
    "total_chunks": 4,
    "chunks_size": 1000,
    "fps": 15,
    "splits": {
        "train": "0:3603"
    },
    "data_path": "data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet",
    "video_path": "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
    "features": {
        "observation.images.rgb_static": {
            "dtype": "video",
            "shape": [
                150,
                200,
                3
            ],
            "names": [
                "height",
                "width",
                "channel"
            ],
            "video_info": {
                "video.fps": 15.0,
                "video.codec": "av1",
                "video.pix_fmt": "yuv420p",
                "video.is_depth_map": false,
                "has_audio": false
            }
        },
        "observation.images.rgb_gripper": {
            "dtype": "video",
            "shape": [
                84,
                84,
                3
            ],
            "names": [
                "height",
                "width",
                "channel"
            ],
            "video_info": {
                "video.fps": 15.0,
                "video.codec": "av1",
                "video.pix_fmt": "yuv420p",
                "video.is_depth_map": false,
                "has_audio": false
            }
        },
        "language_instruction": {
            "dtype": "string",
            "shape": [
                1
            ],
            "names": null
        },
        "observation.state": {
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
            }
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
            }
        },
        "timestamp": {
            "dtype": "float32",
            "shape": [
                1
            ],
            "names": null
        },
        "episode_index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null
        },
        "frame_index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null
        },
        "next.reward": {
            "dtype": "float32",
            "shape": [
                1
            ],
            "names": null
        },
        "next.done": {
            "dtype": "bool",
            "shape": [
                1
            ],
            "names": null
        },
        "index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null
        },
        "task_index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null
        }
    }
}
```


## Citation

**BibTeX:**

```bibtex
@inproceedings{rosete2022tacorl,
    author = {Erick Rosete-Beas and Oier Mees and Gabriel Kalweit and Joschka Boedecker and Wolfram Burgard},
    title = {Latent Plans for Task Agnostic Offline Reinforcement Learning},
    journal = {Proceedings of the 6th Conference on Robot Learning (CoRL)},
    year = {2022}
}
@inproceedings{mees23hulc2,
    title={Grounding  Language  with  Visual  Affordances  over  Unstructured  Data},
    author={Oier Mees and Jessica Borja-Diaz and Wolfram Burgard},
    booktitle = {Proceedings of the IEEE International Conference on Robotics and Automation (ICRA)},
    year={2023},
    address = {London, UK}
}
```