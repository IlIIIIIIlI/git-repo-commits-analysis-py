## 🔍 Technical Highlights

This commit introduces several significant changes to the project, particularly around the deployment of a Chroma database instance using AWS CloudFormation, an update to the deployment script, and a minor refactor of the Drawer component in the frontend codebase.

### AWS CloudFormation Changes

- A new AWS CloudFormation template (`agent.cf.json`) has been added to the `aws/cf` directory. This template defines the infrastructure required to run a Chroma instance hosted on AWS EC2.
- The template specifies several parameters, such as `KeyName`, `InstanceType`, and `ChromaVersion`, allowing users to customize their deployment.
- It includes conditions to check if a key name is provided for SSH access.
- The resources defined in the template include an EC2 instance (`ChromaInstance`) and a security group (`ChromaInstanceSecurityGroup`).
- The EC2 instance is configured with user data scripts to install Docker, Docker Compose, and set up the Chroma server along with ClickHouse, which is the database implementation being used.
- The security group is set up to allow ingress traffic on ports 22 (SSH) and 8000 (Chroma server).
- Outputs are declared to provide the server's public IP address post-deployment.
- A mapping section (`Region2AMI`) defines AMIs and root device names for different AWS regions, ensuring the template can choose the appropriate AMI based on the deployment region.

### Deployment Script Changes

- A new deployment script (`deploy.sh`) has been added to the `aws/cf` directory.
- This bash script navigates to its directory and then triggers the AWS CloudFormation stack creation using the `agent.cf.json` template.

### Frontend Drawer Component Refactor

- The `Drawer.tsx` file, which seems to be part of the frontend React application, has been refactored.
- A conditional rendering has been simplified for displaying a message when there are no agents (`agents.length === 0`). The ternary operator has been replaced with a logical AND.
- The `className` property of the `DrawerItem` component has been refactored to use the `clsx` library for conditional class assignment, replacing the template string with a more readable syntax.

## 📝 Context

This commit is focused on setting up an automated infrastructure deployment for a Chroma database instance on AWS. The CloudFormation template is tailored to provision all necessary components, including the EC2 instance, security configurations, and database setup. Additionally, the deployment script provides an easy way to create the stack from the command line.

The changes to the `Drawer.tsx` file suggest ongoing UI improvements in the application, with a focus on clean and maintainable code.

Overall, the commit reflects a substantial progression towards automating the deployment process and improving the maintainability of the codebase.