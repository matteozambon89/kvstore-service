# Instructions for running locally with `glgroup localdev`

## Setting up your local dev environment

- Clone the [gds.clusterconfig.dev](https://github.com/glg/gds.clusterconfig.dev/) repository to your local machine.
- Checkout a personal branch (as you would for the [starphleet-dev](https://github.com/glg/ec2.starphleet.dev.headquarters) repo)
- Copy the contents of the [localdev-cc folder](../localdev-cc) into the folder you have cloned the `gds.clusterconfig.dev` repo into. **DO NOT** copy the `localdev-cc` folder itself, just the contents. You do not need to copy the `README` nor `local.env.sample` files!
- Install the [`localdev-plus` package](https://github.com/glg/localdev-plus/blob/main/README.md) globally if not done before via `npm install -g @glg/localdev-plus`
- (_optional_) Merge the [aws-cli/setup](./aws-cli/setup) content to the `aws-cli/setup` in your copy of `gds.clusterconfig.dev`
- Merge the [override.yaml](./override.yaml) content to the `override.yaml` in your copy of `gds.clusterconfig.dev`
- Merge the [local.env.sample](./local.env.sample) content to the `local.env` in your copy of `gds.clusterconfig.dev`
- Ensure to have at least the variables marked with `@required` uncommented and updated

You should be ready to build and deploy your localdev version now

## Running the local dev environment

- Open two terminal windows. In one navigate to the root of this repository, in the other navigate to where you have cloned the `gds.clusterconfig.dev` repository.
- In the first terminal run:
  - `./docker-build.sh` - be patient, this can take 3-4 minutes to build completely
- Once the image has built above, in the second terminal run _\*_:
  - `ld+ enable` and select `aws-cli`, `dynamodb`, `kvstore` and `localstack` from the list
  - `ld+ bootstrap`
  - `./kvstore/setup.sh`

> \* note: these steps typically only need to be run once, when you first configure the localdev environment. You will need to run again if you change any of the orders files but this should be rare. If you do change the orders files in the `gds.clusterconfig.dev` repository, please copy your changes back to this repository for future reference. Be aware of storing/removing secrets, file locations etc in the version in this repository.
